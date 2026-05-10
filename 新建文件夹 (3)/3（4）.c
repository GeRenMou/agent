#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    int n;
    scanf("%d", &n);

    if (n >= 90) {
        printf("A级");
    }
    else if (n < 90 && n >= 80) {
        printf("B级");
    }
    else if (n < 80 && n >= 70) {
        printf("C级");
    }
    else if (n < 70 && n >= 60) {
        printf("D级");
    }
    else if (n < 60) {
        printf("E级");
    }
    return 0;
}