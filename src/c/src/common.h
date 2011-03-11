/*
 * common.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */

#define FALSE 0
#define TRUE 1

#ifdef RCCE

#define SEND(B, L, D) iRCCE_isend((B), (L), (D), send_requests)
#define RECV(B, L, S) iRCCE_irecv((B), (L), (S), recv_requests)

#else

#define SEND(B, L, D) sock_send((D), (B), (L))
#define RECV(B, L, S) sock_recv((S), (B), (L))

#endif



#ifdef RCCE

#include "RCCE.h"
#include "iRCCE.h"

#else

// we'll fake out RCCE using sockets
#include "sock-common.h"

#endif


typedef struct {
	uint8_t source;
	char *msg_body;
} message_t;


#if 0
/**
 * Stub main function in case anyone ever tries to run this directly.
 */
int main(int argc, char **argv) {

	// This shouldn't usually be called
	printf("Use libciel-scc as a shared library; it cannot be run directly. Exiting.\n");

	return EXIT_SUCCESS;

}
#endif
