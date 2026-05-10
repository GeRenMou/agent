#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    int n;
    scanf("%d", &n);

    if (n / 2 == 0) {
        printf("%d是偶数", n);
    }
    else {
        printf("%d是奇数", n);
    }
    return 0;
}