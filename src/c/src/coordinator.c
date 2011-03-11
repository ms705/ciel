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

	printf("socket-based emulation mode, setting up %d sockets\n", num_cores);

	if(sock_init(&s, FALSE) > 1) {
		perror("Failed to set up coordinator socket, exiting");
		exit(1);
	}

    printf("coordinator socket set up\n");

#endif

    printf("coord_init() finished");

}


message_t coord_read(void) {

    char buf[1024];
    int n_recv;
    message_t msg;

#ifdef RCCE

    iRCCE_RECV_REQUEST* finisher_request;


    // XXX hardcoded remote rank
    /*if (RECV(buf, sizeof(buf), 1) != iRCCE_SUCCESS) {
    	while (iRCCE_isend_test(recv_requests, NULL) != iRCCE_SUCCESS) {}
    }*/

    recv_requests = (iRCCE_RECV_REQUEST*)malloc(num_cores*sizeof(iRCCE_RECV_REQUEST));

    for (i=1; i < num_cores; i++) {
    	iRCCE_irecv(buf, sizeof(buf), i, &recv_requests[i]);
    	iRCCE_add_to_wait_list(&general_waitlist, NULL, &recv_requests[i]);
    }

    // Use iRCCE_wait_any() function:
	iRCCE_wait_any(&general_waitlist, NULL, &finisher_request);

	printf("got a message from core %d: %s\n", finisher_request->source, buf);

    msg.source = finisher_request->source;
    msg.msg_body = buf;

    return msg;

#else
    n_recv = RECV(buf, sizeof(buf), s);

    if (n_recv > 0)
    	printf("%s\n", buf);
#endif


}

// send_message()

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
