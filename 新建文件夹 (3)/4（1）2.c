#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    int i = 1;
    int s = 0;
    while (i <= 100) {
        s = s + i;
        i++;
    }
    printf("%d", s);
    return 0;
}