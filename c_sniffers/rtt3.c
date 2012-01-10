#define APP_NAME		"sniffex"
#define APP_DESC		"Sniffer example using libpcap"
#define APP_COPYRIGHT	"Copyright (c) 2005 The Tcpdump Group"
#define APP_DISCLAIMER	"THERE IS ABSOLUTELY NO WARRANTY FOR THIS PROGRAM."
#define MAX_SIZE 100

/*
    http://stackoverflow.com/questions/523724/c-c-check-if-one-bit-is-set-in-i-e-int-variable
*/   
#define CHECK_BIT(var,pos) ((var) & (1<<(pos)))

#include <pcap.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <time.h>

/* default snap length (maximum bytes per packet to capture) */
#define SNAP_LEN 1518

/* ethernet headers are always exactly 14 bytes [1] */
#define SIZE_ETHERNET 14

/* Ethernet addresses are 6 bytes */
#define ETHER_ADDR_LEN	6

/* Ethernet header */

int g_waiting = 0;
u_int g_total_data = 0;
u_int g_sequence_num = 0;
char *g_dest_address = NULL;
time_t g_start = 0.0;
time_t g_end = 0.0;
u_int g_size_payload = 0;
u_short g_window_size = 0;

u_int seq_arr[MAX_SIZE];
time_t seq_time_arr[MAX_SIZE];
time_t ack_time_arr[MAX_SIZE];
int arr_index = 0;

struct sniff_ethernet {
        u_char  ether_dhost[ETHER_ADDR_LEN];    /* destination host address */
        u_char  ether_shost[ETHER_ADDR_LEN];    /* source host address */
        u_short ether_type;                     /* IP? ARP? RARP? etc */
};

/* IP header */
struct sniff_ip {
        u_char  ip_vhl;                 /* version << 4 | header length >> 2 */
        u_char  ip_tos;                 /* type of service */
        u_short ip_len;                 /* total length */
        u_short ip_id;                  /* identification */
        u_short ip_off;                 /* fragment offset field */
        #define IP_RF 0x8000            /* reserved fragment flag */
        #define IP_DF 0x4000            /* dont fragment flag */
        #define IP_MF 0x2000            /* more fragments flag */
        #define IP_OFFMASK 0x1fff       /* mask for fragmenting bits */
        u_char  ip_ttl;                 /* time to live */
        u_char  ip_p;                   /* protocol */
        u_short ip_sum;                 /* checksum */
        struct  in_addr ip_src, ip_dst;  /* source and dest address */
};
#define IP_HL(ip)               (((ip)->ip_vhl) & 0x0f)
#define IP_V(ip)                (((ip)->ip_vhl) >> 4)

/* TCP header */
typedef u_int tcp_seq;

struct sniff_tcp {
        u_short th_sport;               /* source port */
        u_short th_dport;               /* destination port */
        tcp_seq th_seq;                 /* sequence number */
        tcp_seq th_ack;                 /* acknowledgement number */
        u_char  th_offx2;               /* data offset, rsvd */
#define TH_OFF(th)      (((th)->th_offx2 & 0xf0) >> 4)
        u_char  th_flags;
        #define TH_FIN  0x01
        #define TH_SYN  0x02
        #define TH_RST  0x04
        #define TH_PUSH 0x08
        #define TH_ACK  0x10
        #define TH_URG  0x20
        #define TH_ECE  0x40
        #define TH_CWR  0x80
        #define TH_FLAGS        (TH_FIN|TH_SYN|TH_RST|TH_ACK|TH_URG|TH_ECE|TH_CWR)
        u_short th_win;                 /* window */
        u_short th_sum;                 /* checksum */
        u_short th_urp;                 /* urgent pointer */
};

void
got_packet(u_char *args, const struct pcap_pkthdr *header, const u_char *packet);

void
print_payload(const u_char *payload, int len);

void
print_hex_ascii_line(const u_char *payload, int len, int offset);

void
print_app_banner(void);

void
print_app_usage(void);

/*
 * app name/banner
 */
void
print_app_banner(void)
{

	printf("%s - %s\n", APP_NAME, APP_DESC);
	printf("%s\n", APP_COPYRIGHT);
	printf("%s\n", APP_DISCLAIMER);
	printf("\n");

return;
}

/*
 * print help text
 */
void
print_app_usage(void)
{

	printf("Usage: %s [interface]\n", APP_NAME);
	printf("\n");
	printf("Options:\n");
	printf("    interface    Listen on <interface> for packets.\n");
	printf("\n");

return;
}

/*
 * dissect/print packet
 */
void got_packet(u_char *args, const struct pcap_pkthdr *header, const u_char *packet)    {
	
	/* declare pointers to packet headers */
	const struct sniff_ethernet *ethernet;  /* The ethernet header [1] */
	const struct sniff_ip *ip;              /* The IP header */
	const struct sniff_tcp *tcp;            /* The TCP header */
	const char *payload;                    /* Packet payload */

	int size_ip;
	int size_tcp;
	int size_payload;

    int ack = 0;
    int syn = 0;
    u_int sequence_num;
    u_int ack_num;
    u_short window_size;
    float rtt = 0.0;
    char *src_address;
    char *dest_address;
    int i = 0;

	/* define ethernet header */
	ethernet = (struct sniff_ethernet*)(packet);
	
	/* define/compute ip header offset */
	ip = (struct sniff_ip*) (packet + SIZE_ETHERNET);
	size_ip = IP_HL(ip)*4;
	if (size_ip < 20) {
		printf("   * Invalid IP header length: %u bytes\n", size_ip);
		return;
	}
	
	/* determine protocol */	
	switch(ip->ip_p) {
		case IPPROTO_TCP:
			printf("\n      Protocol: TCP\n");
			break;
		case IPPROTO_UDP:
			printf("   Protocol: UDP\n");
			return;
		case IPPROTO_ICMP:
			printf("   Protocol: ICMP\n");
			return;
		case IPPROTO_IP:
			printf("   Protocol: IP\n");
			return;
		default:
			printf("   Protocol: unknown\n");
			return;
	}
	
	/*
	 *  OK, this packet is TCP.
	 */
	
	/* define/compute tcp header offset */
	tcp = (struct sniff_tcp*) (packet + SIZE_ETHERNET + size_ip);
	size_tcp = TH_OFF(tcp)*4;
	if (size_tcp < 20) {
		printf("   * Invalid TCP header length: %u bytes\n", size_tcp);
		return;
	}
	
	/* define/compute tcp payload (segment) offset */
	payload = (u_char *)(packet + SIZE_ETHERNET + size_ip + size_tcp);
	
	/* compute tcp payload (segment) size */
	size_payload = ntohs(ip->ip_len) - (size_ip + size_tcp);

	u_int flags = tcp->th_flags;
    /*
	u_char ack = 0;
	u_char syn = 0;
	ack = CHECK_BIT(flags, 4);
    syn = CHECK_BIT(flags, 1);
    */
    if (CHECK_BIT(flags, 4) == 16)
        ack = 1;
    if (CHECK_BIT(flags, 2) == 2)
        syn = 1;

    src_address = inet_ntoa(ip->ip_src);
    dest_address = inet_ntoa(ip->ip_dst);
    window_size = tcp->th_win;
    sequence_num = tcp->th_seq;
    ack_num = tcp->th_ack;

    if (strcmp(dest_address, g_dest_address) == 0)    {
        //An outgoing packet. Record sequence number and timestamp.
        seq_time_arr[arr_index] = time(NULL);
        seq_arr[arr_index] = sequence_num;
    }
    arr_index++;
    if (arr_index == MAX_SIZE)  {
        exit(EXIT_FAILURE);
        for (i=0; i++; i<MAX_SIZE)  {
            printf("%u\n", seq_arr[i]);
        }
    }

    /*
    if (!g_waiting && syn != 2 && size_payload != 0)   {
        if (strcmp(dest_address, g_dest_address) == 0)   {
            g_sequence_num = sequence_num;

            printf("Sequence number %u recorded \n", sequence_num);
            printf("Payload size is: %u\n", size_payload);
            //printf("Expected ACK number is: %u\n", sequence_num + size_payload);
            printf("\n");

            g_waiting = 1;
            g_start = time(NULL);
            g_size_payload = size_payload;
        }
    } else  if (g_waiting && syn != 2 && size_payload == 0)   {
        if (strcmp(src_address, g_dest_address) == 0)    {

            printf("flag%u\n", ack);
            printf("Checking ack %u with payload size: %u\n", ack_num, size_payload);
            printf("Window: %u\n", window);

            if (ack_num == g_sequence_num + g_size_payload)   {
                //this is the expected ack
                g_end = time(NULL);
                rtt = difftime(g_end, g_start);
                printf("Time: %f\n", rtt);

                //TODO append stop time to an array?
                g_waiting = 0;
                printf("\n");
            } else if (ack_num == g_sequence_num)  {
                //packet must be resent
                g_start = time(NULL);
                printf("Timeout???");
                g_waiting = 0;
                printf("\n");
            } else if (ack_num > g_sequence_num + g_size_payload)   {
                //printf("Difference is: %u\n", (ack_num - (g_sequence_num + g_size_payload)));
                g_waiting = 0;
                //printf("\n");
            }
        }
    }
    */

    return;
}

int main(int argc, char **argv)
{

    char *dev = NULL;			/* capture device name */
	char errbuf[PCAP_ERRBUF_SIZE];		/* error buffer */
	pcap_t *handle;				/* packet capture handle */

    //TODO filters on tcp instead of ip
	char filter_exp[] = "tcp";		/* filter expression [3] */
	struct bpf_program fp;			/* compiled filter program (expression) */
	bpf_u_int32 mask;			/* subnet mask */
	bpf_u_int32 net;			/* ip */
	int num_packets = -1;			/* number of packets to capture */

	print_app_banner();

	/* check for capture device name on command-line */
	if (argc == 2) {
		//dev = argv[1];
	}
	else if (argc > 2) {
		dev = argv[1];
        g_dest_address = argv[2];
	}
    else if (argc > 3)  {
		fprintf(stderr, "error: unrecognized command-line options\n\n");
		print_app_usage();
		exit(EXIT_FAILURE);
    }
	else {
		/* find a capture device if not specified on command-line */
		dev = pcap_lookupdev(errbuf);
		if (dev == NULL) {
			fprintf(stderr, "Couldn't find default device: %s\n",
			    errbuf);
			exit(EXIT_FAILURE);
		}
	}
	
	/* get network number and mask associated with capture device */
	if (pcap_lookupnet(dev, &net, &mask, errbuf) == -1) {
		fprintf(stderr, "Couldn't get netmask for device %s: %s\n",
		    dev, errbuf);
		net = 0;
		mask = 0;
	}

	/* print capture info */
	printf("Device: %s\n", dev);
	printf("Number of packets: %d\n", num_packets);
	printf("Filter expression: %s\n", filter_exp);

	/* open capture device */
    //TODO iv'e disabled promiscuous mode
	handle = pcap_open_live(dev, SNAP_LEN, 0, 1000, errbuf);
	if (handle == NULL) {
		fprintf(stderr, "Couldn't open device %s: %s\n", dev, errbuf);
		exit(EXIT_FAILURE);
	}

	/* make sure we're capturing on an Ethernet device [2] */
	if (pcap_datalink(handle) != DLT_EN10MB) {
		fprintf(stderr, "%s is not an Ethernet\n", dev);
		exit(EXIT_FAILURE);
	}

	/* compile the filter expression */
	if (pcap_compile(handle, &fp, filter_exp, 0, net) == -1) {
		fprintf(stderr, "Couldn't parse filter %s: %s\n",
		    filter_exp, pcap_geterr(handle));
		exit(EXIT_FAILURE);
	}

	/* apply the compiled filter */
	if (pcap_setfilter(handle, &fp) == -1) {
		fprintf(stderr, "Couldn't install filter %s: %s\n",
		    filter_exp, pcap_geterr(handle));
		exit(EXIT_FAILURE);
	}

	/* now we can set our callback function */
	pcap_loop(handle, num_packets, got_packet, NULL);

	/* cleanup */
	pcap_freecode(&fp);
	pcap_close(handle);

	printf("\nCapture complete.\n");

    return 0;
}

