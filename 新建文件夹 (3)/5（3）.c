#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>

int main() {
    int a[7] = { 2, 5, 8, 9, 12, 25, 26 };
    int n;
    printf("输入一个直线上的坐标:");
    scanf("%d", &n);

    int b = 0, c = a[0] - n, d = 0;
    if (c < 0) {
        c = c * (-1);
    }

    for (int i = 0; i < 7; i++) {
        b = n - a[i];
        if (b < 0) {
            b = b * (-1);
        }
        if (b < c) {
            c = b;
            d = i;
        }
    }

    printf("%d", a[d]);
    return 0;
}