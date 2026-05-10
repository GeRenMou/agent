#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    for (int n = 100; n <= 200; n++) {
        if (n % 3 == 0) {
            printf("%d ", n);
        }
    }
    return 0;
}