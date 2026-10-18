/* Independent-set search on graphs with at most 64 vertices.
 *
 * find_indep(n, adj, t, maxout, out, seed): enumerate independent sets of
 * size exactly t (stopping after maxout of them), writing each as a
 * vertex bitmask into out[]. Returns the number found. The search is
 * complete: a return value of 0 proves alpha(G) < t.
 *
 * Upper bound used for pruning: any matching M in G[cand] covers cand by
 * |cand| - |M| cliques, so alpha(G[cand]) <= |cand| - |M|.
 */
#include <stdint.h>

typedef uint64_t u64;

static int n_;
static const u64 *adj_;
static int t_;
static int maxout_;
static u64 *out_;
static int nout_;
static int order_[64];

static inline int popc(u64 x) { return __builtin_popcountll(x); }

static int matching_bound(u64 cand) {
    int m = 0;
    u64 left = cand;
    while (left) {
        int v = __builtin_ctzll(left);
        left &= left - 1;
        u64 nb = adj_[v] & left;
        if (nb) {
            int u = __builtin_ctzll(nb);
            left &= ~(1ULL << u);
            m++;
        }
    }
    return popc(cand) - m;
}

static void rec(u64 cur, int size, u64 cand) {
    if (nout_ >= maxout_) return;
    if (size == t_) { out_[nout_++] = cur; return; }
    int need = t_ - size;
    if (popc(cand) < need) return;
    if (matching_bound(cand) < need) return;
    /* branch on the first candidate in the randomized order */
    int v = -1;
    for (int i = 0; i < n_; i++) {
        if (cand >> order_[i] & 1) { v = order_[i]; break; }
    }
    u64 bit = 1ULL << v;
    rec(cur | bit, size + 1, cand & ~adj_[v] & ~bit);
    if (nout_ >= maxout_) return;
    rec(cur, size, cand & ~bit);
}

int find_indep(int n, const u64 *adj, int t, int maxout, u64 *out, u64 seed) {
    n_ = n; adj_ = adj; t_ = t; maxout_ = maxout; out_ = out; nout_ = 0;
    for (int i = 0; i < n; i++) order_[i] = i;
    if (seed) { /* xorshift shuffle for diversity of reported sets */
        u64 s = seed;
        for (int i = n - 1; i > 0; i--) {
            s ^= s << 13; s ^= s >> 7; s ^= s << 17;
            int j = (int)(s % (u64)(i + 1));
            int tmp = order_[i]; order_[i] = order_[j]; order_[j] = tmp;
        }
    }
    u64 all = (n == 64) ? ~0ULL : ((1ULL << n) - 1);
    rec(0, 0, all);
    return nout_;
}

/* alpha(G) by repeated calls is wasteful; this computes it directly. */
static int best_;
static void rec_alpha(int size, u64 cand) {
    if (cand == 0) { if (size > best_) best_ = size; return; }
    if (size + matching_bound(cand) <= best_) return;
    int v = __builtin_ctzll(cand);
    u64 bit = 1ULL << v;
    rec_alpha(size + 1, cand & ~adj_[v] & ~bit);
    rec_alpha(size, cand & ~bit);
}

int alpha(int n, const u64 *adj) {
    n_ = n; adj_ = adj; best_ = 0;
    u64 all = (n == 64) ? ~0ULL : ((1ULL << n) - 1);
    rec_alpha(0, all);
    return best_;
}

/* Independent s-sets S with |N(S)| < need (domination violations).
 * Writes up to maxout vertex masks into out; returns the count. */
static int s_, need_, dmax_, dn_;
static u64 *dout_;
static void rec_dom(u64 cur, int size, u64 cand, u64 nb) {
    if (dn_ >= dmax_) return;
    if (size == s_) {
        if (popc(nb) < need_) dout_[dn_++] = cur;
        return;
    }
    while (cand) {
        int v = __builtin_ctzll(cand);
        u64 bit = 1ULL << v;
        cand &= ~bit;
        rec_dom(cur | bit, size + 1, cand & ~adj_[v], nb | adj_[v]);
        if (dn_ >= dmax_) return;
    }
}

int find_dom_violations(int n, const u64 *adj, int s, int need, int maxout, u64 *out) {
    n_ = n; adj_ = adj; s_ = s; need_ = need; dmax_ = maxout; dout_ = out; dn_ = 0;
    u64 all = (n == 64) ? ~0ULL : ((1ULL << n) - 1);
    rec_dom(0, 0, all, 0);
    return dn_;
}
