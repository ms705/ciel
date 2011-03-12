/*
 ============================================================================
 Name        : rcce-coordinator.c
 Author      : Malte Schwarzkopf
 Version     :
 Copyright   : (c) 2011 Malte Schwarzkopf
 Description :
 ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <stdint.h>

#include "coordinator.h"

//int num_ranks, remote_rank, my_rank;
#ifdef RCCE

iRCCE_WAIT_LIST general_waitlist;

iRCCE_RECV_REQUEST *recv_requests;
iRCCE_SEND_REQUEST *send_requests;

#else

int s; 			// socket descriptor

#endif

uint8_t num_cores;

void coord_init(int argc, char **argv) {

	num_cores = atoi(argv[1]);

#ifdef RCCE

	printf("RCCE enabled for %d cores\n", num_cores);

	RCCE_init(&argc, &argv);
	printf("RCCE init done\n");

	iRCCE_init();
	printf("iRCCE init done\n");

	//RCCE_barrier(&RCCE_COMM_WORLD);

    iRCCE_init_wait_list(&general_waitlist);
	printf("waitlist init done\n");

#else

	printf("socket-based emulation mode, setting up sockets\n");

	sock_set_id(0);

	if(sock_init_server(&s, TRUE) > 1) {
		perror("Failed to set up coordinator socket, exiting");
		exit(1);
	}

    printf("coordinator socket set up\n");

#endif

    printf("coord_init() finished\n");

}


message_t coord_read(void) {

    char *buf;
    int n_recv, msg_size;
    //message_t *msg = (message_t *)malloc(sizeof(message_t));
    message_t msg;

    msg.dest = COORDINATOR_CORE;

#ifdef RCCE

    iRCCE_RECV_REQUEST* finisher_request;
    int i;

    // XXX hardcoded remote rank
    /*if (RECV(buf, sizeof(buf), 1) != iRCCE_SUCCESS) {
    	while (iRCCE_isend_test(recv_requests, NULL) != iRCCE_SUCCESS) {}
    }*/

    recv_requests = (iRCCE_RECV_REQUEST*)malloc(num_cores*sizeof(iRCCE_RECV_REQUEST));

    for (i=1; i < num_cores; i++) {
    	iRCCE_irecv((char *)&msg_size, sizeof(uint32_t), i, &recv_requests[i]);
    	iRCCE_add_to_wait_list(&general_waitlist, NULL, &recv_requests[i]);
    }

    // Use iRCCE_wait_any() function:
	iRCCE_wait_any(&general_waitlist, NULL, &finisher_request);

	printf("got a message of length %d from core %d\n", msg_size, finisher_request->source);

	// Now actually receive the message (in blocking mode)
	buf = (char *)malloc(msg_size*sizeof(char));
	iRCCE_recv(buf, msg_size, finisher_request->source);

    msg.source = finisher_request->source;
    msg.msg_body = buf;

    free(recv_requests);

#else
    n_recv = RECV((char *)&msg_size, sizeof(uint32_t), s);
    assert(n_recv == sizeof(uint32_t));

    printf("message size %d returned\n", msg_size);

	buf = (char *)malloc((msg_size+1)*sizeof(char));
    n_recv = RECV(buf, msg_size, s);

    // Need to explicitly add null termination?
    //buf[msg_size] = '\0';

    //printf("got message\n", msg_size);

    if (n_recv > 0)
    	printf("%s\n", buf);

    msg.source = COORDINATOR_CORE; // XXX need to fix this
    msg.msg_body = buf;

#endif

    msg.length = msg_size;

    return msg;

}


void coord_send(message_t msg) {

	uint32_t len = msg.length;

#ifdef RCCE

	// Send length of message first so that the other end knows what buffer size to allocate
	SEND_B((char *)&len, sizeof(uint32_t), msg.dest);

	// Now send the actual message body
	SEND_B(msg.msg_body, len, msg.dest);

#else

	// Send length of message first so that the other end knows what buffer size to allocate
	SEND_B((char *)&len, sizeof(uint32_t), msg.dest);

	// Now send the actual message body
	SEND_B(msg.msg_body, len, msg.dest);

#endif

}

// wait_for_receive() ?

// start_exec()


void coord_quit(void) {

	printf("RCCE coordinator quitting\n");

#ifdef RCCE
#else
	// close the socket
	close(s);
#endif

	exit(0);

}

void coord_hello(void) {

	printf("Hello from the RCCE coordinator!\n");

}
