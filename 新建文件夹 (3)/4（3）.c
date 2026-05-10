#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#define PI 3.14159

int main() {
    float s = 0;
    for (float n = 1; n <= 10; n++) {
        s = PI * n * n;
        if (s >= 100) {
            break;
        }
        printf("%f\n", s);
    }
    return 0;
}