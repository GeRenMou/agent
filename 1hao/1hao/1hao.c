#include<stdio.h>
int main() {
    int n;
    scanf("%d", n);
    char arr[100][100] = { 0 };
    int m = n / 2;
    int x;
    int y;

    for (x = 0; x < n; x++) {
        for (y = 0; y < n; y++) {
            arr[x][y] = ' ';
        }
    }
    for (x = 0; x < m; x++) {
        for (y = m - x; y <= x + m; y++) {
            arr[x][y] = '*';
        }
    }
    for (y = 0; y < m; y++) {
        arr[m][y] = '*';
    }
    for (x = m + 1; x < n; x++) {
        for (y = x - m; y < n + m - x; y++) {
            arr[x][y] = '*';
        }
    }
    for (x = 0; x < n; x++) {
        for (y = 0; y < n; y++) {
            printf("%c", arr[x][y]);
        }
        printf("\n");
    }

    return 0;
}