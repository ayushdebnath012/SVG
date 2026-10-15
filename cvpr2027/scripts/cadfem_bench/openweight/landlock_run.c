/* landlock_run: run a command under a Landlock ruleset (unprivileged, kernel-enforced; Linux >= 5.13).
 *
 *   landlock_run [--ro PATH]... [--rw PATH]... -- PROGRAM [ARGS]...
 *
 * Every filesystem access right the kernel's Landlock ABI knows is handled, so anything not granted below is denied.
 * --ro grants read and execute beneath PATH; --rw grants every handled right beneath PATH. TCP bind and connect are
 * handled with no rule, so all TCP is denied (ABI >= 4). Abstract UNIX sockets and signals are scoped to the sandbox
 * (ABI >= 6). no_new_privs is set first. Used by the CADFEM-Bench open-weight harness, because the shared host denies
 * unprivileged user/network namespaces (AppArmor) and Docker.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/types.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

#ifndef __NR_landlock_create_ruleset
#define __NR_landlock_create_ruleset 444
#define __NR_landlock_add_rule 445
#define __NR_landlock_restrict_self 446
#endif

struct ruleset_attr { __u64 handled_access_fs, handled_access_net, scoped; };
struct path_beneath_attr { __u64 allowed_access; __s32 parent_fd; } __attribute__((packed));

#define FS_EXECUTE (1ULL << 0)
#define FS_WRITE_FILE (1ULL << 1)
#define FS_READ_FILE (1ULL << 2)
#define FS_READ_DIR (1ULL << 3)
#define FS_REFER (1ULL << 13)
#define FS_TRUNCATE (1ULL << 14)
#define FS_IOCTL_DEV (1ULL << 15)
#define NET_BIND_TCP (1ULL << 0)
#define NET_CONNECT_TCP (1ULL << 1)
#define SCOPE_ABSTRACT_UNIX (1ULL << 0)
#define SCOPE_SIGNAL (1ULL << 1)
#define FILE_RIGHTS (FS_EXECUTE | FS_WRITE_FILE | FS_READ_FILE | FS_TRUNCATE | FS_IOCTL_DEV)

static int add(int rfd, const char *path, __u64 rights, __u64 handled) {
    int fd = open(path, O_PATH | O_CLOEXEC);
    if (fd < 0) { fprintf(stderr, "landlock_run: skip %s (%s)\n", path, strerror(errno)); return 0; }
    struct stat st;
    fstat(fd, &st);
    struct path_beneath_attr pb = { .allowed_access = rights & handled, .parent_fd = fd };
    if (!S_ISDIR(st.st_mode)) pb.allowed_access &= FILE_RIGHTS;
    int r = syscall(__NR_landlock_add_rule, rfd, 1 /* LANDLOCK_RULE_PATH_BENEATH */, &pb, 0);
    close(fd);
    if (r) { fprintf(stderr, "landlock_run: add_rule %s: %s\n", path, strerror(errno)); return -1; }
    return 0;
}

int main(int argc, char **argv) {
    int abi = syscall(__NR_landlock_create_ruleset, NULL, 0, 1 /* VERSION */);
    if (abi < 1) { fprintf(stderr, "landlock_run: Landlock unavailable (%s); refusing to run unsandboxed\n", strerror(errno)); return 125; }
    __u64 fs = (1ULL << 13) - 1;                       /* ABI 1 rights: EXECUTE .. MAKE_SYM */
    if (abi >= 2) fs |= FS_REFER;
    if (abi >= 3) fs |= FS_TRUNCATE;
    if (abi >= 5) fs |= FS_IOCTL_DEV;
    struct ruleset_attr ra = { .handled_access_fs = fs, .handled_access_net = abi >= 4 ? NET_BIND_TCP | NET_CONNECT_TCP : 0,
                               .scoped = abi >= 6 ? SCOPE_ABSTRACT_UNIX | SCOPE_SIGNAL : 0 };
    size_t sz = abi >= 6 ? sizeof ra : abi >= 4 ? 2 * sizeof(__u64) : sizeof(__u64);
    int rfd = syscall(__NR_landlock_create_ruleset, &ra, sz, 0);
    if (rfd < 0) { perror("landlock_run: create_ruleset"); return 125; }
    int i = 1;
    for (; i < argc; i++) {
        if (!strcmp(argv[i], "--")) { i++; break; }
        if (i + 1 >= argc) { fprintf(stderr, "landlock_run: missing path after %s\n", argv[i]); return 125; }
        if (!strcmp(argv[i], "--ro")) { if (add(rfd, argv[++i], FS_EXECUTE | FS_READ_FILE | FS_READ_DIR, fs)) return 125; }
        else if (!strcmp(argv[i], "--rw")) { if (add(rfd, argv[++i], fs, fs)) return 125; }
        else { fprintf(stderr, "landlock_run: unknown option %s\n", argv[i]); return 125; }
    }
    if (i >= argc) { fprintf(stderr, "usage: landlock_run [--ro P]... [--rw P]... -- PROG [ARGS]\n"); return 125; }
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) { perror("landlock_run: no_new_privs"); return 125; }
    if (syscall(__NR_landlock_restrict_self, rfd, 0)) { perror("landlock_run: restrict_self"); return 125; }
    close(rfd);
    execvp(argv[i], argv + i);
    perror("landlock_run: exec");
    return 127;
}
