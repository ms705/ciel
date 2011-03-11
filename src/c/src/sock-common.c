
#include "sock-common.h"

int sock_init(int *sock, uint8_t blocking) {

    register int len;
    struct sockaddr_un saun;


    // Get a streaming UNIX domain socket
    if ((*sock = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
    	perror("socket creation error");
    	return 1;
    }

    // Create the address to connect to
    saun.sun_family = AF_UNIX;
    strcpy(saun.sun_path, SOCK_ADDR);

    // delete the socket file if it still exists
    unlink(SOCK_ADDR);

    len = sizeof(saun.sun_family) + strlen(saun.sun_path);

    if (bind(*sock, (const struct sockaddr *)&saun, len) < 0) {
    	perror("failed to bind to socket");
    	return 1;
    }

    if (listen(*sock, 5) < 0) {
    	perror("failed to listen on socket");
    	return 1;
    }

    // Make the socket non-blocking
    if (!blocking) sock_set_nonblock(*sock);

    return 0;
}


void sock_send(int sockfd, char *data, size_t len) {

	send(sockfd, data, len, 0);

}

int32_t sock_recv(int sockfd, char *buf, unsigned int len) {

	struct sockaddr_un from_saun;
	socklen_t from_len;
    int32_t rval;
    int32_t n_read = 0;

    int msgsock = accept(sockfd, (const struct sockaddr *)&from_saun, &from_len);
    if (msgsock == -1)
            //perror("accept failed");
			return -1;
    else do {
            memset(buf, 0, len);
            if ((rval  = read(msgsock, buf,  len)) < 0)
                    //perror("reading stream message");
					n_read += rval;
            //i = 0;
            if (rval == 0)
                    printf("Ending connection\n");
            else
                    printf("-->%s\n", buf);
    } while (rval != 0);
    close(msgsock);

    printf("read %d bytes", n_read);

    return n_read;
}


void sock_set_nonblock(int socket) {
	int flags;
	flags = fcntl(socket,F_GETFL,0);
	assert(flags != -1);
	fcntl(socket, F_SETFL, flags | O_NONBLOCK);
}

#if 0
void copy_data(int srcFD, int destFD) {

	char buf[1024];
	int count;
	while ((count=read(srcFD, buf, sizeof(buf)))>0) {

		if (write(destFD, buf, count)!=count) {
			perror("write");
			exit(1);
		}
	}

	if (count<0) {
		perror("read");
		exit(1);
	}

}
#endif
