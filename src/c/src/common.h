/*
 * common.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */


#ifdef RCCE

#define SEND(B, L, D) iRCCE_isend((B), (L), (D), &send_request)

#else

#define SEND(B, L, D) sock_send((D), (B), (L))

#endif



#ifdef RCCE

#include <iRCCE.h>

// The master core ID -- TODO: this shouldn't be hardcoded
#define MASTER 0

#else

// we'll fake out RCCE using sockets
#include "sock-common.h"

#define MASTER "libciel-scc-socket"

#endif
