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
#include <assert.h>

#include "coordinator.h"

//int num_ranks, remote_rank, my_rank;
#ifdef RCCE

iRCCE_WAIT_LIST general_waitlist;
uint8_t waitlist_initialized;

iRCCE_RECV_REQUEST *recv_requests;
iRCCE_SEND_REQUEST *send_requests;

extern iRCCE_RECV_REQUEST** iRCCE_irecv_queue;

#else

int s;		// socket descriptor

#endif

uint8_t num_cores;
uint8_t last_finisher;


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
    waitlist_initialized = 0;
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
	int n_recv;
	static uint32_t msg_size;
	//message_t *msg = (message_t *)malloc(sizeof(message_t));
	message_t msg;
	uint8_t i;

	msg.dest = COORDINATOR_CORE;

#ifdef RCCE

	iRCCE_RECV_REQUEST* finisher_request;

	// XXX hardcoded remote rank
	/*if (RECV(buf, sizeof(buf), 1) != iRCCE_SUCCESS) {
		while (iRCCE_isend_test(recv_requests, NULL) != iRCCE_SUCCESS) {}
	}*/

	if (!waitlist_initialized) {
		// Initialize the wait list and populate it with a non-blocking read request for every core
		recv_requests = (iRCCE_RECV_REQUEST*)malloc(num_cores*sizeof(iRCCE_RECV_REQUEST));

		for (i=1; i < num_cores; i++) {
			iRCCE_irecv((char *)&msg_size, sizeof(uint32_t), i, &recv_requests[i]);
			iRCCE_add_to_wait_list(&general_waitlist, NULL, &recv_requests[i]);
			//printf("WL_INIT non-blocking recv from core %d initiated\n", i);
		}
		waitlist_initialized = 1;
	} else {
		// We have just serviced a request, so we better make sure we replace it with a new one
		iRCCE_irecv((char *)&msg_size, sizeof(uint32_t), last_finisher, &recv_requests[last_finisher]);
		iRCCE_add_to_wait_list(&general_waitlist, NULL, &recv_requests[last_finisher]);
		//printf("WL_REPLACE non-blocking recv from core %d initiated\n", last_finisher);
	}

	// Use iRCCE_wait_any() function:
	iRCCE_wait_any(&general_waitlist, NULL, &finisher_request);

	printf("got a message of length %d from core %d\n", msg_size, finisher_request->source);

	// Now actually receive the message (in blocking mode)
	buf = (char *)malloc(msg_size*sizeof(char));
	iRCCE_recv(buf, msg_size, finisher_request->source);

	msg.source = finisher_request->source;
	msg.msg_body = buf;
	last_finisher = msg.source;


#else
	n_recv = RECV((char *)&msg_size, sizeof(uint32_t), s);
	assert(n_recv == sizeof(uint32_t));

	printf("message size %d returned\n", msg_size);

	buf = (char *)malloc((msg_size)*sizeof(char));
	n_recv = RECV(buf, msg_size, s);

	/*if (n_recv > 0)
		printf("%s\n", buf);*/

	msg.source = 1; // XXX need to fix this
	msg.msg_body = buf;

	printf("got message from %d\n", msg.source);

#endif

	msg.length = msg_size;

	return msg;

}


void coord_send(message_t msg) {

	uint32_t len = msg.length;

	//printf("coordinator sending message of len %d to core %d: %s\n", len, msg.dest, msg.msg_body);
	printf("coordinator sending message of len %d to core %d\n", len, msg.dest);

	// Send length of message first so that the other end knows what buffer size to allocate
	SEND_B((char *)&len, sizeof(uint32_t), msg.dest);

	// Now send the actual message body
	SEND_B(msg.msg_body, len, msg.dest);

}


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
