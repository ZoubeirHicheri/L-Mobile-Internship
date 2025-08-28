// == Inject CSS ==
fetch(chrome.runtime.getURL("content.css"))
  .then(r => r.text())
  .then(css => {
    const styleTag = document.createElement('style');
    styleTag.textContent = css;
    document.head.appendChild(styleTag);
  });

// == Inject Widget HTML ==
fetch(chrome.runtime.getURL("widget.html"))
  .then(r => r.text())
  .then(html => {
    // Replace icon src dynamically
    const iconUrl = chrome.runtime.getURL("icon.png");
    html = html.replaceAll("__ICON_URL__", iconUrl);
    const aiWidgetDiv = document.createElement('div');
    aiWidgetDiv.innerHTML = html;
    document.body.appendChild(aiWidgetDiv);

    // == References ==
    const widget = document.getElementById("ai-chatbot-draggable");
    const header = document.getElementById("ai-chatbot-header");
    const fab = document.getElementById("ai-chatbot-fab");
    const minBtn = document.getElementById("ai-chatbot-min");

    // == FAB Show/Hide + Drag/Click Disambiguation ==
    let isFabDragging = false,
        fabStartX, fabStartY, fabStartLeft, fabStartTop,
        fabDragMoved = false;

    // Drag: move FAB
    fab.addEventListener("mousedown", function(e) {
      if (e.button !== 0) return;
      isFabDragging = true;
      fabDragMoved = false; // reset
      e.preventDefault();
      fabStartX = e.clientX;
      fabStartY = e.clientY;
      fabStartLeft = parseInt(fab.style.left, 10) || fab.getBoundingClientRect().left;
      fabStartTop = parseInt(fab.style.top, 10) || fab.getBoundingClientRect().top;
      fab.style.right = "unset";
      fab.style.bottom = "unset";
      document.onmousemove = function(ev) {
        if (isFabDragging) {
          let dx = ev.clientX - fabStartX;
          let dy = ev.clientY - fabStartY;
          fab.style.left = (fabStartLeft + dx) + "px";
          fab.style.top = (fabStartTop + dy) + "px";
          if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
            fabDragMoved = true;
          }
        }
      };
      document.onmouseup = function() {
        isFabDragging = false;
        document.onmousemove = null;
        document.onmouseup = null;
      };
    });
    // Only open chat if FAB wasn't dragged
    fab.addEventListener("click", function(e) {
      if (fabDragMoved) {
        e.preventDefault();
        fabDragMoved = false;
        return; // prevent opening on drag-end
      }
      widget.style.display = "flex";
      fab.style.display = "none";
      const rect = widget.getBoundingClientRect();
      // Place widget at FAB's last known position
      widget.style.left = (parseInt(fab.style.left, 10) || window.innerWidth - rect.width - 30) + "px";
      widget.style.top = (parseInt(fab.style.top, 10) || window.innerHeight - rect.height - 90) + "px";
      widget.style.right = "unset";
      widget.style.bottom = "unset";
    });

    // == Widget Minimize ==
    minBtn.onclick = () => {
      widget.style.display = "none";
      fab.style.display = "flex";
    };

    // == Widget Dragging ==
    let isDraggingWidget = false, widgetStartX, widgetStartY, widgetStartLeft, widgetStartTop;
    header.addEventListener("mousedown", function(e) {
      if (e.button !== 0) return;
      isDraggingWidget = true;
      widgetStartX = e.clientX;
      widgetStartY = e.clientY;
      widgetStartLeft = parseInt(widget.style.left, 10) || widget.getBoundingClientRect().left;
      widgetStartTop = parseInt(widget.style.top, 10) || widget.getBoundingClientRect().top;

      document.onmousemove = function(ev) {
        if (isDraggingWidget) {
          let dx = ev.clientX - widgetStartX;
          let dy = ev.clientY - widgetStartY;
          widget.style.left = (widgetStartLeft + dx) + "px";
          widget.style.top = (widgetStartTop + dy) + "px";
          widget.style.right = "unset";
          widget.style.bottom = "unset";
        }
      };
      document.onmouseup = function() {
        isDraggingWidget = false;
        document.onmousemove = null;
        document.onmouseup = null;
      };
    });

    // == Chat Logic ==
    const chatLog = document.getElementById("ai-chatbot-log");
    const form = document.getElementById("ai-chatbot-input-row");
    const userInputElem = document.getElementById("ai-chatbot-input");

    form.addEventListener("submit", async e => {
      e.preventDefault();
      const userInput = userInputElem.value.trim();
      if (!userInput) return;

      // Add user bubble
      chatLog.innerHTML += `<div class="bubble user">${userInput}</div>`;
      chatLog.scrollTop = chatLog.scrollHeight;
      userInputElem.value = "";

      // Show bot thinking bubble
      const thinkingBubble = document.createElement('div');
      thinkingBubble.className = 'bubble bot';
      thinkingBubble.textContent = '...';
      chatLog.appendChild(thinkingBubble);
      chatLog.scrollTop = chatLog.scrollHeight;

      // Call bot API (replace/add Authorization header if needed)
      try {
        const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer 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',
          },
          body: JSON.stringify({
            model: "openai/gpt-oss-20b:free",
            messages: [
              { role: "system", content: "You are a helpful assistant." },
              {role: "user", content: userInput}
            ]
          })
        });
        let botReply = "Sorry, I didn't get a response.";
        if (response.ok) {
          const data = await response.json();
          botReply = data.choices?.[0]?.message?.content || botReply;
        } else {
          botReply = "API error. Try again later.";
        }
        thinkingBubble.remove();
        chatLog.innerHTML += `<div class="bubble bot">${botReply}</div>`;
        chatLog.scrollTop = chatLog.scrollHeight;
      } catch (error) {
        thinkingBubble.remove();
        chatLog.innerHTML += `<div class="bubble bot">Network error.</div>`;
        chatLog.scrollTop = chatLog.scrollHeight;
      }
    });
  });