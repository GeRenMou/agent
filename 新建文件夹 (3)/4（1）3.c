#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    int i = 1;
    int s = 0;
    do {
        s = s + i;
        i++;
    } while (i <= 100);
    printf("%d", s);
    return 0;
}