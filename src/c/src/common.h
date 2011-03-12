/*
 * common.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */

#define FALSE 0
#define TRUE 1

#define COORDINATOR_CORE 0

#ifdef RCCE

#define SEND(B, L, D) iRCCE_isend((B), (L), (D), send_requests)
#define SEND_B(B, L, D) iRCCE_send((B), (L), (D))
#define RECV(B, L, S) iRCCE_irecv((B), (L), (S), recv_requests)

#else

#define SEND(B, L, D) sock_send((D), (B), (L))   // TODO: this isn't necessarily non-blocking at the moment
#define SEND_B(B, L, D) sock_send((D), (B), (L)) // TODO: this isn't necessarily blocking at the moment
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
	uint32_t source;
	uint32_t dest;
	uint32_t length;
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
