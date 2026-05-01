# Documentation Example (Tilde Fence)

The following block uses CommonMark tilde fencing for the code block.
The inner aac: markers must be ignored by the validator.

~~~markdown
<!-- aac:generated source=docs/diagrams/system.c4 view=L1 -->
Diagram content would appear here.
<!-- aac:end -->
~~~

Outside the tilde block, a valid authored region:

<!-- aac:authored owner=bob -->
This is real authored content outside the tilde code block.
<!-- aac:end -->
