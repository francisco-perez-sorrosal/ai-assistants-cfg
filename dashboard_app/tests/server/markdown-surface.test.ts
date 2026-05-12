import { describe, expect, it } from "vitest";

import { prepareMarkdownBody } from "@/components/markdown-surface";

describe("prepareMarkdownBody — HTML comment stripping", () => {
  it("strips a single HTML comment", () => {
    const input = "before\n<!-- a comment -->\nafter";
    expect(prepareMarkdownBody(input)).toBe("before\n\nafter");
  });

  it("strips multi-line HTML comments", () => {
    const input = "<!-- OWNER: doc-engineer\n   some text\n-->\n# Heading";
    expect(prepareMarkdownBody(input)).not.toContain("<!--");
    expect(prepareMarkdownBody(input)).not.toContain("OWNER:");
    expect(prepareMarkdownBody(input)).toContain("# Heading");
  });

  it("strips multiple comments in one pass", () => {
    const input = "<!-- A -->\nprose\n<!-- B -->";
    const result = prepareMarkdownBody(input);
    expect(result).not.toContain("<!--");
    expect(result).toContain("prose");
  });
});

describe("prepareMarkdownBody — raw <img> to markdown image conversion", () => {
  it("converts a double-quoted <img src alt> to markdown image syntax", () => {
    const input = '<img src="/api/diagram?path=x" alt="My diagram">';
    const result = prepareMarkdownBody(input);
    expect(result).toBe('![My diagram](/api/diagram?path=x)');
  });

  it("converts a single-quoted <img src alt> to markdown image syntax", () => {
    const input = "<img src='diagrams/foo.svg' alt='Foo'>";
    const result = prepareMarkdownBody(input);
    expect(result).toBe("![Foo](diagrams/foo.svg)");
  });

  it("handles <img> with no alt attribute (empty alt)", () => {
    const input = '<img src="diagrams/context.svg">';
    const result = prepareMarkdownBody(input);
    expect(result).toBe("![](diagrams/context.svg)");
  });

  it("handles self-closing <img /> syntax", () => {
    const input = '<img src="/api/diagram?path=x" alt="y" />';
    const result = prepareMarkdownBody(input);
    expect(result).toBe("![y](/api/diagram?path=x)");
  });

  it("leaves existing markdown image syntax ![z](w) untouched", () => {
    const input = "![Architecture](diagrams/components.svg)";
    expect(prepareMarkdownBody(input)).toBe("![Architecture](diagrams/components.svg)");
  });

  it("leaves prose untouched", () => {
    const prose = "# Heading\n\nSome paragraph with no images.";
    expect(prepareMarkdownBody(prose)).toBe(prose);
  });

  it("strips comment AND converts img in the same body", () => {
    const input =
      '<!-- OWNER: systems-architect -->\n\n<img src="../docs/diagrams/architecture/rendered/context.svg" alt="Praxion System Context (L0)" />\n\nSome prose.';
    const result = prepareMarkdownBody(input);
    expect(result).not.toContain("<!--");
    expect(result).not.toContain("<img");
    expect(result).toContain("![Praxion System Context (L0)](../docs/diagrams/architecture/rendered/context.svg)");
    expect(result).toContain("Some prose.");
  });
});
