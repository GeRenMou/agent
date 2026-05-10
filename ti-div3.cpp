#include<bits/stdc++.h>
using namespace std;

int main(){
	int n , m;
	cin >> n >> m;
	vector<int> a(n);
	
	for(int i = 0 ; i < n ; i++) cin >> a[i];
	for(int i = 0 ; i < m ; i++){
		int t;
		cin >> t;
		int left = 0 , right = n - 1;
		while(left < right){
			int tmp = a[(right + left + 1) / 2];
			if(t > tmp) left = tmp + 1;
			else if(t < tmp) right = tmp - 1;
			else if(t == tmp)cout << " " << (right + left + 1) / 2;
			else cout << " -1";
		}
	}
	 
	return 0;
} 
