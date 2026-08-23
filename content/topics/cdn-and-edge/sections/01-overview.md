# Overview
A CDN replicates content to Points of Presence worldwide. Users hit nearby PoPs, cutting RTT from hundreds of milliseconds to single digits and offloading origin bandwidth entirely for cacheable assets.

Beyond static files, modern CDNs terminate TLS, normalize HTTP/2/3, shield origins, enforce WAF rules, and run compute at the edge (Workers/Lambda@Edge) for personalization without central round trips. For global products the CDN *is* the front door - designing headers, purging strategy and origin health with that in mind separates smooth launches from origin-melting ones.
