/*
 * rcce-coordinator.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */

#ifndef COORDINATOR_H
#define COORDINATOR_H

#include "common.h"

#ifndef RCCE
static int coord_sock_init();
#endif

void coord_init(int argc, char **argv);
void coord_read(void);
void coord_quit(void);
void coord_hello(void);


#endif /* COORDINATOR_H */
