import type { ConversationMessage } from "../../types";
import {
  leafForBranch,
  siblingPosition,
  siblingsOf,
} from "../../utils/conversationTree";

interface Props {
  messages: ConversationMessage[];
  message: ConversationMessage;
  onNavigate: (leafId: string) => void;
}

/** Branch switcher: ◀ 2/3 ▶ — jumps to the newest leaf of the chosen branch. */
export function SiblingNav({ messages, message, onNavigate }: Props) {
  const { index, count } = siblingPosition(messages, message.id);
  if (count < 2) return null;
  const siblings = siblingsOf(messages, message.id);

  const jump = (nextIndex: number) => {
    const target = siblings[nextIndex];
    if (!target) return;
    const leaf = leafForBranch(messages, target.id);
    if (leaf) onNavigate(leaf.id);
  };

  return (
    <span className="sibling-nav">
      <button
        disabled={index <= 1}
        onClick={() => jump(index - 2)}
        aria-label="previous branch"
      >
        ◀
      </button>
      <span>
        {index}/{count}
      </span>
      <button
        disabled={index >= count}
        onClick={() => jump(index)}
        aria-label="next branch"
      >
        ▶
      </button>
    </span>
  );
}
