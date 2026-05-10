#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    char a, b, c = 0;
    int d = 0;
    scanf("%c%c", &a, &b);
    c = a + b;
    d = a + b;
    printf("%c+%c=%c\n", a, b, c);
    printf("%c+%c=%d\n", a, b, d);
    return 0;
}
