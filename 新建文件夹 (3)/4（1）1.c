#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    int i = 1;
    int s = 0;
    for (i = 1; i <= 100; i++) {
        s = s + i;
    }
    printf("%d", s);
    return 0;
}