#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    int a[5] = { 0 };
    for (int i = 0; i < 5; i++) {
        scanf("%d", &a[i]);
    }
    int b = 0;
    for (int i = 0; i < 5; i++) {
        if (b < a[i]) {
            b = a[i];
        }
    }
    printf("%d", b);
    return 0;
}