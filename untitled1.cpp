#include<bits/stdc++.h>
using namespace std;

void solve(){
	string a;
	cin >> a;
	int jug = 0;
	char tmp = a[0];
	for(int i = 1 ; i < a.size() ; i++){
		if(a[i] == tmp){
			jug++;
		} 
		tmp = a[i];
	}
	if(jug >= 3) cout << "NO\n";
	else cout <<"YES\n";
}

int main(){
	int t;cin >> t;
	while(t--) solve();
	
	return 0;
}
