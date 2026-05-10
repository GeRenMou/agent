#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
int large(int x, int y) {
    if (x > y) {
        return x;
    }
    else {
        return y;
    }
}

int main() {
    int a[10] = { 0 };
    for (int i = 0; i < 10; i++) {
        scanf("%d", &a[i]);
    }
    int b = 0;
    for (int i = 0; i < 10; i++) {
        b = large(b, a[i]);
    }
    printf("%d", b);
    return 0;
}