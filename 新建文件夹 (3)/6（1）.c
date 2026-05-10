#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
#define PI 3.14159

double area(double x) {
    double c;
    c = PI * x * x;
    return c;
}

int main() {
    double a;
    scanf("%lf", &a);
    double c = area(a);
    printf("%lf", c);
    return 0;
}