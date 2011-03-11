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
void coord_read();
void coord_quit();
void coord_hello();


#endif /* COORDINATOR_H */
