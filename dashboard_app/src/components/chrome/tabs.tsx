"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";

export type TabItem = {
  content: ReactNode;
  id: string;
  label: string;
};

export function Tabs({
  initialTabId,
  tabs
}: {
  initialTabId?: string;
  tabs: TabItem[];
}) {
  const firstTabId = tabs[0]?.id ?? "";
  const [activeId, setActiveId] = useState<string>(initialTabId ?? firstTabId);
  const tabRefs = useRef<Map<string, HTMLButtonElement>>(new Map());

  useEffect(() => {
    if (initialTabId !== undefined) {
      setActiveId(initialTabId);
    }
  }, [initialTabId]);

  function handleKeyDown(event: React.KeyboardEvent<HTMLButtonElement>, tabId: string) {
    const ids = tabs.map((tab) => tab.id);
    const currentIndex = ids.indexOf(tabId);

    let nextId: string | undefined;

    if (event.key === "ArrowRight") {
      nextId = ids[(currentIndex + 1) % ids.length];
    } else if (event.key === "ArrowLeft") {
      nextId = ids[(currentIndex - 1 + ids.length) % ids.length];
    } else if (event.key === "Home") {
      nextId = ids[0];
    } else if (event.key === "End") {
      nextId = ids[ids.length - 1];
    }

    if (nextId !== undefined) {
      event.preventDefault();
      setActiveId(nextId);
      tabRefs.current.get(nextId)?.focus();
    }
  }

  const activeTab = tabs.find((tab) => tab.id === activeId) ?? tabs[0];

  return (
    <div className="tabs">
      <div className="tabs__list" role="tablist">
        {tabs.map((tab) => (
          <button
            aria-controls={`tabpanel-${tab.id}`}
            aria-selected={tab.id === activeId}
            className={`tabs__tab${tab.id === activeId ? " is-active" : ""}`}
            id={`tab-${tab.id}`}
            key={tab.id}
            onClick={() => { setActiveId(tab.id); }}
            onKeyDown={(event) => { handleKeyDown(event, tab.id); }}
            ref={(el) => {
              if (el) {
                tabRefs.current.set(tab.id, el);
              } else {
                tabRefs.current.delete(tab.id);
              }
            }}
            role="tab"
            tabIndex={tab.id === activeId ? 0 : -1}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      {tabs.map((tab) => (
        <div
          aria-labelledby={`tab-${tab.id}`}
          className="tabs__panel"
          hidden={tab.id !== activeId}
          id={`tabpanel-${tab.id}`}
          key={tab.id}
          role="tabpanel"
          tabIndex={0}
        >
          {activeTab?.id === tab.id ? tab.content : null}
        </div>
      ))}
    </div>
  );
}
