#include <bits/stdc++.h>
using namespace std;

int maxSubarray(vector<int>& a) {
    int best = 0, cur = 0;
    for (int x : a) {
        cur = max(0, cur + x);
        best = max(best, cur);
    }
    return best;
}
