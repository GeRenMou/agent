#include <stdio.h>

int main() {
    int n ;
    int m ;
    int sum1=0;
    scanf("%d",&n );
    scanf("%d\n",&m );
    
    int arr1[n];
   
    int i; 
    for(i = 0; i < n; i++) {
        scanf("%d", &arr1[i]); 
    }
    
    int arr2[m];
    
    int j;
    for(j = 0; j < m; j++) {
        scanf("%d", &arr2[j]); 
    }
    
    
    for(i = 0; i < n; i++) {
        sum1+=arr1[i];
    }
    int sum2=arr2[0];
    for(j = 0; j < m; j++){
        if(arr2[j]>sum2){
        	sum2=arr2[j];
		}
    }
    if (sum1>sum2){
    	printf("Yes");
    
	}
    else{printf("No");
	}
    
    return 0;
}
