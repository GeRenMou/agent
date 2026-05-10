#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
int main() {
    int a;
    scanf("%d", &a);
    int b, c, d;
    d = a / 100;        
    c = (a % 100) / 10; 
    b = a % 10;         
    printf("%d\n%d\n%d\n", d, c, b);
    return 0;
}