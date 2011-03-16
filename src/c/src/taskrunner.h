/*
 * rcce-worker.h
 *
 *  Created on: 9 Mar 2011
 *      Author: ms705
 */

#ifndef TASKRUNNER_H
#define TASKRUNNER_H

#include "common.h"

void tr_init(int argc, char **argv);
void tr_send(message_t *msg);
void tr_hello(void);

#endif /* TASKRUNNER_H */
