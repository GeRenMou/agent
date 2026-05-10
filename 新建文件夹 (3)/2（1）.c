#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
int main() {
    int a = 2, b = 5;
    int c = 0;
    c = a;
    a = b;
    b = c;
    printf("a=%d,b=%d", a, b);
    return 0;
}