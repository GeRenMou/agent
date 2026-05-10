#include <stdio.h>

int main() {
    int n;
    printf("请输入数组大小：");
    scanf("%d", &n);

    int arr[n];

    // 输入数组元素
    printf("请输入%d个整数：\n", n);
    for (int i = 0; i < n; i++) {
        printf("arr[%d] = ", i);
        scanf("%d", &arr[i]);  // 注意：需要取地址符&
    }

    // 输出验证
    printf("数组内容：");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }

    return 0;
}