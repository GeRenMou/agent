#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
int main() {
    int n;
    scanf("%d", &n);
    if (n > 0) {
        printf("%d", n);
    }
    else {
        printf("%d", n * (-1));
    }
    return 0;
}