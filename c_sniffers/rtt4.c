#define __USE_BSD 
#define __FAVOR_BSD

#define APP_NAME		"sniffex"
#define APP_DESC		"Sniffer example using libpcap"
#define APP_COPYRIGHT	"Copyright (c) 2005 The Tcpdump Group"
#define APP_DISCLAIMER	"THERE IS ABSOLUTELY NO WARRANTY FOR THIS PROGRAM."
#define MAX_SIZE 20

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
#include <sys/time.h>

/* default snap length (maximum bytes per packet to capture) */
#define SNAP_LEN 1518

/* ethernet headers are always exactly 14 bytes [1] */
#define SIZE_ETHERNET 14

/* Ethernet addresses are 6 bytes */
#define ETHER_ADDR_LEN	6

/* Ethernet header */

char *g_dest_address = NULL;
char *g_src_address = NULL;
unsigned int seq_arr[MAX_SIZE];
unsigned int ack_arr[MAX_SIZE];
struct timeval seq_time_arr[MAX_SIZE];
struct timeval ack_time_arr[MAX_SIZE];
int seq_counter = 0;
int ack_counter = 0;

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

	printf("Usage: %s <interface> <source ip address> <destination ip address> <number of packets to examine>\n", APP_NAME);
	printf("\n");

return;
}

void match()    {
    int i = 0;
    int j = 0;
    int k = 0;
    int seq_found = 0;
    double rtt = 0;
    char rtt_string[25];
    unsigned int sequence_num = 0;
    int seq_index = 0;

    FILE *file;
    file = fopen("rtt.txt", "a+"); //open for reading and writing (append if file exists)

    for (i = 0; i < MAX_SIZE; i++)  {
        //iterate over the ACK numbers
        if (ack_arr[i] == 0)
            break;
        seq_found = 0;
        sequence_num = 0;
        seq_index = 0;
        for (j = 0; j < MAX_SIZE; j++)  {
            //iterate over the Sequences numbers
            if (seq_arr[j] == 0)
                break;
            if (seq_arr[j] == ack_arr[i])   {
                //an ACK was matched to a sequence number, find the next smallest sequence number
                seq_found = 1;
                for (k = 0; k < MAX_SIZE; k++)  {
                    if (seq_arr[k] < seq_arr[j] && seq_arr[k] > sequence_num)   {
                        sequence_num = seq_arr[k];
                        seq_index = k;
                    }
                }
                break;
            }
        }
        if (!seq_found || sequence_num == 0)    {
            printf("Ack %u could not be matched. Continuing on to next ACK.\n", ack_arr[i]);
            continue;
        }
        printf("Last sequence number to go out before ACK %u was sequence %u\n", ack_arr[i], sequence_num);
        printf("Number of bytes transmitted by said sequence number: %u\n", ack_arr[i] - sequence_num);
        rtt = (double) (ack_time_arr[i].tv_usec - seq_time_arr[seq_index].tv_usec);
        sprintf(rtt_string, "%f\n", rtt);
        fwrite(rtt_string, sizeof(rtt_string[0]), strlen(rtt_string), file);
        printf("Time difference is: %f microseconds\n", rtt);
        printf("\n");
    }
    fclose(file);
}

void clear()    {
    int i = 0;

    for (i = 0; i < MAX_SIZE; i++)  {
        seq_arr[i] = 0;
    }
    for (i = 0; i < MAX_SIZE; i++)  {
        ack_arr[i] = 0;
    }
    memset(seq_time_arr, 0, sizeof(struct timeval)*MAX_SIZE);
    memset(ack_time_arr, 0, sizeof(struct timeval)*MAX_SIZE);
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
    int fin = 0;

    tcp_seq seq_num;
    tcp_seq ack_num;

    u_short window_size;
    float rtt = 0.0;
    char src_address[20];
    char dest_address[20];

    int t_result = -1;

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
			//printf("\n      Protocol: TCP\n");
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

    if (CHECK_BIT(flags, 4) == 16)
        ack = 1;
    if (CHECK_BIT(flags, 1) == 2)
        syn = 1;
    if (CHECK_BIT(flags, 0) == 1)
        fin = 1;

    strcpy(src_address, inet_ntoa(ip->ip_src));
    strcpy(dest_address, inet_ntoa(ip->ip_dst));

    //http://www.gnu.org/software/libc/manual/html_node/Byte-Order.html
    window_size = ntohs(tcp->th_win);
    seq_num = ntohl(tcp->th_seq);
    ack_num = ntohl(tcp->th_ack);
 
    //TODO check for fin and syn in these if statements???
    if (strcmp(dest_address, g_dest_address) == 0 && strcmp(src_address, g_src_address) == 0 && size_payload != 0) {
        //this is an outgoing packet with a payload, record the sequence number
        seq_arr[seq_counter] = seq_num;
        //TODO check on t_result?
        t_result = gettimeofday(&(seq_time_arr[seq_counter++]), NULL);
    }
    else if (strcmp(dest_address, g_src_address) == 0 && strcmp(src_address, g_dest_address) == 0 && size_payload == 0) {
        //this is an incoming packet without a payload, record the ack number
        ack_arr[ack_counter] = ack_num;
        //TODO check on t_result?
        t_result = gettimeofday(&(ack_time_arr[ack_counter++]), NULL);
    }

    if (ack_counter == MAX_SIZE-1 || seq_counter == MAX_SIZE-1) {
        match();
       
        //TODO does clear even have an effect here?
        clear();
        
        ack_counter = 0;
        seq_counter = 0;
    }

    return;
}

int main(int argc, char **argv) {

    char *dev = NULL;			/* capture device name */
	char errbuf[PCAP_ERRBUF_SIZE];		/* error buffer */
	pcap_t *handle;				/* packet capture handle */

    //TODO filters on tcp instead of ip
	char filter_exp[] = "tcp";		/* filter expression [3] */
	struct bpf_program fp;			/* compiled filter program (expression) */
	bpf_u_int32 mask;			/* subnet mask */
	bpf_u_int32 net;			/* ip */
	int num_packets = -1;			/* number of packets to capture */
    int running = 1;

    FILE *file;
    file = fopen("rtt.txt", "w+"); //open for reading and writing (overwrite existing file)
    fclose(file);

    clear();

	print_app_banner();

	/* check for capture device name on command-line */
	if (argc > 3) {
		dev = argv[1];
        g_src_address = argv[2];
        g_dest_address = argv[3];
        num_packets = atoi(argv[4]);
	}
    else if (argc > 4 || argc <= 3)  {
		fprintf(stderr, "error: unrecognized command-line options\n\n");
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
    printf("Source address is %s and Destination address is %s\n", g_src_address, g_dest_address);

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

	pcap_loop(handle, num_packets, got_packet, NULL);

	/* cleanup */
	pcap_freecode(&fp);
	pcap_close(handle);

	printf("\nCapture complete.\n");

    return 0;
}
