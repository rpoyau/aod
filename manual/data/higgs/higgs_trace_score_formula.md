# Higgs Trace Score Formula — No Candidate Override

This score is a trace-detector score. It must not branch on candidate identity.

For candidate \(K=(p,q,L)\):

\[
\Pi=q^p+q,\quad RD=2\Pi+1,\quad
\rho^D_\omega=\min(RD,L),
\]

\[
P^D_H=C_{3,H}\rho^D_\omega,\qquad
Q^D_H=C_{3,H}\max(0,RD-L).
\]

For the lower/upper closure band \(C_a,C_b\), define

\[
\Delta_{\rm lower}=P^D_H-C_a,\qquad
\Delta_{\rm upper}=P^D_H-C_b.
\]

For the current Higgs-support trace detector:

\[
d_{\rm saddle}=|\Delta_{\rm lower}-3|+|\Delta_{\rm upper}+3|,
\]

\[
d_Q(Q^D)=
\begin{cases}
0,&100\le Q^D\le 250,\\
100-Q^D,&Q^D<100,\\
Q^D-250,&Q^D>250,
\end{cases}
\]

\[
d_L=|L-7|,
\]

\[
d_{\rm route}=
\begin{cases}
0,& L=7,\ \Delta_{\rm lower}=3,\ \Delta_{\rm upper}=-3,\ 100\le Q^D\le250,\\
1,&\text{otherwise.}
\end{cases}
\]

Then

\[
S_H(K)=
\frac{d_{\rm saddle}}{12}
+
\frac{d_Q}{100}
+
\frac{d_L}{2}
+
d_{\rm route}.
\]

The score contains no branch of the form

\[
(p,q,L)=(3,3,7).
\]

Regression requirement:

\[
\arg\min_K S_H(K)=3{:}3{:}7_{\rm yro}.
\]
