#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>

int main() {
    float a, b, c = 0.0;
    scanf("%f%f", &a, &b);
    c = a + b;
    printf("%f+%f=%f", a, b, c);
    return 0;
}