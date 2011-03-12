/*
 ============================================================================
 Name        : rcce-taskrunner.c
 Author      : Malte Schwarzkopf
 Version     :
 Copyright   : (c) 2011 Malte Schwarzkopf
 Description :
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <strings.h>
#include <stdint.h>

#include "taskrunner.h"

//int num_ranks, remote_rank, my_rank;
#ifdef RCCE
iRCCE_WAIT_LIST general_waitlist;

iRCCE_RECV_REQUEST *recv_requests;
iRCCE_SEND_REQUEST *send_requests;
#endif


int s; 			// socket descriptor
uint8_t me = 1;


void tr_init(int argc, char **argv) {

#ifdef RCCE

	printf("RCCE enabled\n");

	RCCE_init(&argc, &argv);
	iRCCE_init();

	iRCCE_init_wait_list(&general_waitlist);

#else

	//uint8_t me = atoi(argv[51]);

	printf("me is %d\n", me);

	sock_set_id(me);

	if(sock_init_server(&s, TRUE) > 1) {
		perror("Failed to set up coordinator socket, exiting");
		exit(1);
	}

    printf("task runner sockets set up\n");

#endif

}


void tr_send(void) {

	char c[14];
	int len = sizeof(c);
	bzero(c, len);

	sprintf(c, "Hello world!\n");

	printf("sending message length\n");
	SEND((char *)&len, len, COORDINATOR_CORE);

	printf("sending actual message\n");
	SEND_B(c, len, COORDINATOR_CORE);

}



message_t tr_read(void) {

    char *buf;
    int n_recv, msg_size;
    //message_t *msg = (message_t *)malloc(sizeof(message_t));
    message_t msg;

    msg.dest = COORDINATOR_CORE;

#ifdef RCCE

    // Block waiting for a length to be received
   	iRCCE_recv((char *)&msg_size, sizeof(uint32_t), COORDINATOR_CORE);  // XXX source hard-coded to coordinator

   	// Now actually receive the message
	buf = (char *)malloc(msg_size*sizeof(char));
	iRCCE_recv(buf, msg_size, COORDINATOR_CORE); // XXX source hard-coded to coordinator

    msg.source = COORDINATOR_CORE;  // XXX source hard-coded to coordinator
    msg.msg_body = buf;

#else
    n_recv = RECV((char *)&msg_size, sizeof(uint32_t), s);
    assert(n_recv == sizeof(uint32_t));

    //printf("message size %d returned\n", msg_size);

	buf = (char *)malloc(msg_size*sizeof(char));
    n_recv = RECV(buf, msg_size, s);

    //printf("got message\n", msg_size);

    /*if (n_recv > 0)
    	printf("%s\n", buf);*/

    msg.source = COORDINATOR_CORE;  // XXX source hard-coded to coordinator
    msg.msg_body = buf;

#endif

    msg.length = msg_size;

    return msg;

}


void tr_hello(void) {

	printf("Hello from the RCCE task runner!\n");

}
