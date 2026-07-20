import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MessageBubble } from "./TurnMessages";


describe("MessageBubble", () => {
  it("keeps user content as plain text", () => {
    const { container } = render(
      <MessageBubble role="user" content="**không in đậm** <script>alert(1)</script>" />,
    );

    expect(screen.getByText("**không in đậm** <script>alert(1)</script>")).toBeInTheDocument();
    expect(container.querySelector("strong")).toBeNull();
    expect(container.querySelector("script")).toBeNull();
  });

  it("renders safe Markdown for assistant content", () => {
    const { container } = render(
      <MessageBubble
        role="assistant"
        content={'**in đậm** [OpenAI](https://openai.com) <script>alert(1)</script> ![ảnh](https://example.com/a.png)'}
      />,
    );

    expect(screen.getByText("in đậm").tagName).toBe("STRONG");
    expect(screen.getByRole("link", { name: "OpenAI" })).toHaveAttribute(
      "rel",
      "noopener noreferrer",
    );
    expect(screen.getByText("[Hình ảnh: ảnh]")).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
  });
});
