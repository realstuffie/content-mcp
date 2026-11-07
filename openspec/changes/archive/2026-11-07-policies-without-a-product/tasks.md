## 1. Resolution

- [x] 1.1 Without a product, use the global file, else the only product's file, else raise `AmbiguousControlError`
- [x] 1.2 Expand a product's own policy with that product's variables
- [x] 1.3 Add `products_defining` and `controls_needing_product`

## 2. Tools

- [x] 2.1 Include each product's version in the rule index and similarity search, with `product` on their results
- [x] 2.2 Leave multi-product policies out of searches across all policies without a product, and name them
- [x] 2.3 Describe the behavior in the tool descriptions

## 3. Verification

- [x] 3.1 Unit tests for the global file, one product, several products, the rule index, similarity, and search
- [x] 3.2 Integration tests for `nist_800_53` without a product and the rule index's versions
