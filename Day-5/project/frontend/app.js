// ==================================================
// Configuration
// ==================================================

const API_BASE_URL =
    "http://127.0.0.1:8000";


// ==================================================
// Session
// ==================================================

let sessionId =
    createSessionId();

let conversationListCache = [];


// ==================================================
// DOM Elements
// ==================================================

const chatForm =
    document.getElementById("chatForm");

const messageInput =
    document.getElementById("messageInput");

const sendButton =
    document.getElementById("sendButton");

const chatMessages =
    document.getElementById("chatMessages");

const newChatBtn =
    document.getElementById("newChatBtn");

const fileInput =
    document.getElementById("fileInput");

const uploadStatus =
    document.getElementById("uploadStatus");

const documentList =
    document.getElementById("documentList");

const chatList =
    document.getElementById("chatList");


// ==================================================
// Allowed File Extensions
// ==================================================

const ALLOWED_EXTENSIONS = [
    ".pdf",
    ".txt",
    ".md",
    ".csv",
    ".docx"
];


// ==================================================
// Initial Load
// ==================================================

loadDocuments();
loadConversations();
renderWelcomeState();


// ==================================================
// CHAT
// ==================================================

chatForm.addEventListener(
    "submit",
    async function (event) {

        event.preventDefault();


        const message =
            messageInput.value.trim();


        if (!message) {

            return;
        }


        removeWelcomeMessage();


        addUserMessage(
            message
        );


        messageInput.value = "";

        messageInput.style.height =
            "auto";


        sendButton.disabled =
            true;


        const typingElement =
            addTypingIndicator();


        try {

            const response =
                await fetch(
                    `${API_BASE_URL}/api/chat`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            message:
                                message,

                            session_id:
                                sessionId,

                            file_name: null

                        })
                    }
                );


            const data =
                await response.json();


            typingElement.remove();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Something went wrong."
                );
            }


            addAssistantMessage(

                data.answer,

                data.sources
            );

            await loadConversations();


        } catch (error) {

            typingElement.remove();


            addAssistantMessage(
                `Error: ${error.message}`
            );


        } finally {

            sendButton.disabled =
                false;

            messageInput.focus();
        }
    }
);


// ==================================================
// LOAD CONVERSATIONS
// ==================================================

async function loadConversations() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load conversations."
            );
        }


        conversationListCache =
            data.conversations || [];


        renderConversationList(
            conversationListCache
        );


    } catch (error) {

        console.error(
            "Conversation loading error:",
            error
        );
    }
}

async function renameConversation(conversation) {
    const title = window.prompt(
        "Rename chat",
        conversation.title || "New Chat"
    );
    if (title === null || !title.trim()) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/conversations/${conversation.id}`,
            {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: title.trim() })
            }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not rename chat.");
        await loadConversations();
    } catch (error) {
        window.alert(error.message);
    }
}

async function deleteConversation(conversation) {
    const confirmed = window.confirm(
        `Delete chat "${conversation.title || "New Chat"}" and its messages?`
    );
    if (!confirmed) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/conversations/${conversation.id}`,
            { method: "DELETE" }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not delete chat.");

        if (sessionId === conversation.id) {
            await createNewConversation();
        } else {
            await loadConversations();
        }
    } catch (error) {
        window.alert(error.message);
    }
}


// ==================================================
// RENDER CONVERSATION LIST
// ==================================================

function renderConversationList(
    conversations
) {

    chatList.innerHTML = "";


    if (
        !conversations ||
        conversations.length === 0
    ) {

        chatList.innerHTML = `
            <p class="empty-text">
                No conversations yet
            </p>
        `;

        return;
    }


    conversations.forEach(function (conversation) {
        const item = document.createElement("div");
        item.className = "conversation-item";


        if (
            conversation.id ===
            sessionId
        ) {

            item.classList.add(
                "active"
            );
        }


        const openButton = document.createElement("button");
        openButton.type = "button";
        openButton.className = "conversation-open";
        openButton.innerHTML = `
            <span class="conversation-icon" aria-hidden="true">💬</span>
            <span class="conversation-title">${escapeHtml(conversation.title || "New Chat")}</span>
        `;
        openButton.addEventListener("click", function () {
            openConversation(conversation.id);
        });

        const actions = document.createElement("span");
        actions.className = "conversation-actions";
        actions.innerHTML = `
            <button class="sidebar-icon-btn" type="button" title="Rename chat" aria-label="Rename chat">✎</button>
            <button class="sidebar-icon-btn delete-action" type="button" title="Delete chat" aria-label="Delete chat">🗑️</button>
        `;
        const [renameButton, deleteButton] = actions.querySelectorAll("button");
        renameButton.addEventListener("click", function () {
            renameConversation(conversation);
        });
        deleteButton.addEventListener("click", function () {
            deleteConversation(conversation);
        });

        item.append(openButton, actions);
        chatList.appendChild(item);
    });
}


// ==================================================
// OPEN CONVERSATION
// ==================================================

async function openConversation(
    chatId
) {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations/${chatId}`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Conversation not found."
            );
        }


        sessionId = chatId;

        renderConversationMessages(
            data.messages || []
        );

        await loadConversations();


    } catch (error) {

        console.error(
            "Could not open conversation:",
            error
        );
    }
}


// ==================================================
// RENDER CONVERSATION MESSAGES
// ==================================================

function renderConversationMessages(
    messages
) {

    chatMessages.innerHTML = "";


    if (
        !messages ||
        messages.length === 0
    ) {

        renderWelcomeState();

        return;
    }


    messages.forEach(
        function (message) {

            if (
                message.role ===
                "user"
            ) {

                addUserMessage(
                    message.content
                );

            } else {

                addAssistantMessage(
                    message.content,
                    message.sources || []
                );
            }
        }
    );
}


// ==================================================
// CREATE NEW CONVERSATION
// ==================================================

async function createNewConversation() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/conversations`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not create a new conversation."
            );
        }


        sessionId = data.chat_id;

        renderWelcomeState();

        await loadConversations();


    } catch (error) {

        console.error(
            "Could not create conversation:",
            error
        );
    }
}


// ==================================================
// DOCUMENT UPLOAD
// ==================================================

fileInput.addEventListener(
    "change",
    async function () {

        const file =
            fileInput.files[0];


        if (!file) {

            return;
        }


        const extension =
            getFileExtension(
                file.name
            );


        if (
            !ALLOWED_EXTENSIONS.includes(
                extension
            )
        ) {

            showUploadStatus(
                "Unsupported file type.",
                "error"
            );


            fileInput.value = "";

            return;
        }


        showUploadStatus(
            `Uploading ${file.name}...`,
            "loading"
        );


        try {

            const formData =
                new FormData();


            formData.append(
                "file",
                file
            );


            const response =
                await fetch(
                    `${API_BASE_URL}/api/documents/upload`,
                    {
                        method: "POST",

                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Document upload failed."
                );
            }


            showUploadStatus(
                "Document uploaded and indexed successfully.",
                "success"
            );


            await loadDocuments();


        } catch (error) {

            showUploadStatus(
                `Upload failed: ${error.message}`,
                "error"
            );


        } finally {

            fileInput.value = "";
        }
    }
);


// ==================================================
// Load Documents
// ==================================================

async function loadDocuments() {

    try {

        const response =
            await fetch(
                `${API_BASE_URL}/api/documents`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load documents."
            );
        }


        renderDocuments(
            data.documents
        );


    } catch (error) {

        console.error(
            "Document loading error:",
            error
        );
    }
}


// ==================================================
// Render Documents
// ==================================================

function renderDocuments(documents) {
    documentList.innerHTML = "";

    if (!documents || documents.length === 0) {
        documentList.innerHTML = `
            <p class="empty-text">No documents uploaded</p>
        `;
        return;
    }

    documents.forEach(function (documentInfo) {
        addDocument(documentInfo);
    });
}


function addDocument(documentInfo) {
    const documentElement = document.createElement("div");
    documentElement.className = "document-item";
    documentElement.innerHTML = `
        <span class="document-icon" aria-hidden="true">📄</span>
        <span class="document-name" title="${escapeHtml(documentInfo.path)}">${escapeHtml(documentInfo.path)}</span>
        <button class="sidebar-icon-btn delete-action" type="button" title="Delete document" aria-label="Delete ${escapeHtml(documentInfo.file_name)}">🗑️</button>
    `;
    documentElement.querySelector("button").addEventListener("click", function () {
        deleteDocument(documentInfo);
    });
    documentList.appendChild(documentElement);
}


async function deleteDocument(documentInfo) {
    const confirmed = window.confirm(
        `Permanently delete ${documentInfo.path} and rebuild the document index?`
    );
    if (!confirmed) return;

    showUploadStatus(`Deleting ${documentInfo.file_name}...`, "loading");
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/documents?path=${encodeURIComponent(documentInfo.path)}`,
            { method: "DELETE" }
        );
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not delete document.");

        showUploadStatus(
            `${documentInfo.file_name} and its indexed content were deleted.`,
            "success"
        );
        await loadDocuments();
    } catch (error) {
        showUploadStatus(`Delete failed: ${error.message}`, "error");
    }
}


// ==================================================
// Add User Message
// ==================================================

function addUserMessage(message) {
    const messageElement = document.createElement("div");
    messageElement.className = "message user";
    messageElement.innerHTML = `
        <div class="message-content">${escapeHtml(message)}</div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}


// ==================================================
// Add Assistant Message
// ==================================================

function addAssistantMessage(answer, sources = []) {
    const messageElement = document.createElement("div");
    messageElement.className = "message assistant";
    messageElement.innerHTML = `
        <div class="message-content">${escapeHtml(answer)}</div>
    `;
    chatMessages.appendChild(messageElement);

    if (sources && sources.length > 0) {
        const sourcesElement = document.createElement("div");
        sourcesElement.className = "sources";

        const title = document.createElement("div");
        title.className = "sources-title";
        title.textContent = "Retrieved Sources";
        sourcesElement.appendChild(title);

        sources.forEach(function (source) {
            const sourceElement = document.createElement("div");
            sourceElement.className = "source";
            sourceElement.innerHTML = `
                <div class="source-file">📄 ${escapeHtml(source.file_name)}</div>
                <div class="source-text">${escapeHtml(source.text)}</div>
            `;
            sourcesElement.appendChild(sourceElement);
        });

        chatMessages.appendChild(sourcesElement);
    }

    scrollToBottom();
}


// ==================================================
// Typing Indicator
// ==================================================

function addTypingIndicator() {

    const messageElement =
        document.createElement(
            "div"
        );


    messageElement.className =
        "message assistant";


    messageElement.innerHTML = `
        <div class="message-content">

            <div class="typing">

                <span></span>

                <span></span>

                <span></span>

            </div>

        </div>
    `;


    chatMessages.appendChild(
        messageElement
    );


    scrollToBottom();


    return messageElement;
}


// ==================================================
// Upload Status
// ==================================================

function showUploadStatus(
    message,
    type
) {

    uploadStatus.textContent =
        message;


    uploadStatus.className =
        `upload-status ${type}`;
}


// ==================================================
// File Extension
// ==================================================

function getFileExtension(
    fileName
) {

    const lastDot =
        fileName.lastIndexOf(".");


    if (lastDot === -1) {

        return "";
    }


    return fileName
        .substring(lastDot)
        .toLowerCase();
}


// ==================================================
// Welcome
// ==================================================

function renderWelcomeState() {

    chatMessages.innerHTML = `
        <div class="welcome">

            <div class="welcome-icon">
                🧠
            </div>

            <h2>
                How can I help you?
            </h2>

            <p>
                Upload your company documents
                and ask questions about them.
            </p>

        </div>
    `;

    messageInput.value = "";
    messageInput.style.height = "auto";
    messageInput.focus();
}


function removeWelcomeMessage() {

    const welcome =
        document.querySelector(
            ".welcome"
        );


    if (welcome) {

        welcome.remove();
    }
}


// ==================================================
// New Chat
// ==================================================

newChatBtn.addEventListener(
    "click",
    async function () {

        await createNewConversation();
    }
);


// ==================================================
// Auto Resize
// ==================================================

messageInput.addEventListener(
    "input",
    function () {

        this.style.height =
            "auto";


        this.style.height =
            `${Math.min(
                this.scrollHeight,
                140
            )}px`;
    }
);


// ==================================================
// Enter Key
// ==================================================

messageInput.addEventListener(
    "keydown",
    function (event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            chatForm.requestSubmit();
        }
    }
);


// ==================================================
// Scroll
// ==================================================

function scrollToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// ==================================================
// Session ID
// ==================================================

function createSessionId() {

    if (
        typeof crypto !==
        "undefined" &&
        crypto.randomUUID
    ) {

        return crypto.randomUUID();
    }


    return (
        Date.now().toString(36) +
        Math.random()
            .toString(36)
            .substring(2)
    );
}


// ==================================================
// HTML Safety
// ==================================================

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value ?? "";


    return div.innerHTML;
}