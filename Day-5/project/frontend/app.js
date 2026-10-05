// ==================================================
// Configuration
// ==================================================

const API_BASE_URL = "http://127.0.0.1:8000";


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


        // Remove welcome screen

        removeWelcomeMessage();


        // Display user message

        addUserMessage(message);


        // Clear input

        messageInput.value = "";

        messageInput.style.height = "auto";


        // Disable send button

        sendButton.disabled = true;


        // Show typing indicator

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
                            message: message
                        })
                    }
                );


            const data =
                await response.json();


            // Remove typing indicator

            typingElement.remove();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Something went wrong."
                );
            }


            // Display answer

            addAssistantMessage(
                data.answer,
                data.sources
            );

        } catch (error) {

            typingElement.remove();


            addAssistantMessage(
                `Error: ${error.message}`
            );

        } finally {

            sendButton.disabled = false;

            messageInput.focus();
        }
    }
);


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


        // Check extension

        const extension =
            getFileExtension(file.name);


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


        // Show loading status

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


            // Upload succeeded

            showUploadStatus(
                "Document uploaded and indexed successfully.",
                "success"
            );


            // Add document to sidebar

            addDocument(
                data.file_name
            );


        } catch (error) {

            showUploadStatus(
                `Upload failed: ${error.message}`,
                "error"
            );

        } finally {

            // Allow selecting the same file again

            fileInput.value = "";
        }
    }
);


// ==================================================
// Add User Message
// ==================================================

function addUserMessage(message) {

    const messageElement =
        document.createElement("div");


    messageElement.className =
        "message user";


    messageElement.innerHTML = `
        <div class="message-content">
            ${escapeHtml(message)}
        </div>
    `;


    chatMessages.appendChild(
        messageElement
    );


    scrollToBottom();
}


// ==================================================
// Add Assistant Message
// ==================================================

function addAssistantMessage(
    answer,
    sources = []
) {

    const messageElement =
        document.createElement("div");


    messageElement.className =
        "message assistant";


    messageElement.innerHTML = `
        <div class="message-content">
            ${escapeHtml(answer)}
        </div>
    `;


    chatMessages.appendChild(
        messageElement
    );


    // ----------------------------------------------
    // Sources
    // ----------------------------------------------

    if (
        sources &&
        sources.length > 0
    ) {

        const sourcesElement =
            document.createElement("div");


        sourcesElement.className =
            "sources";


        const title =
            document.createElement("div");


        title.className =
            "sources-title";


        title.textContent =
            "Retrieved Sources";


        sourcesElement.appendChild(
            title
        );


        sources.forEach(
            function (source) {

                const sourceElement =
                    document.createElement("div");


                sourceElement.className =
                    "source";


                sourceElement.innerHTML = `
                    <div class="source-file">
                        📄 ${escapeHtml(
                            source.file_name
                        )}
                    </div>

                    <div class="source-text">
                        ${escapeHtml(
                            source.text
                        )}
                    </div>
                `;


                sourcesElement.appendChild(
                    sourceElement
                );
            }
        );


        chatMessages.appendChild(
            sourcesElement
        );
    }


    scrollToBottom();
}


// ==================================================
// Typing Indicator
// ==================================================

function addTypingIndicator() {

    const messageElement =
        document.createElement("div");


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
// Add Document To Sidebar
// ==================================================

function addDocument(fileName) {

    // Remove empty message

    const emptyText =
        document.querySelector(
            ".document-list .empty-text"
        );


    if (emptyText) {
        emptyText.remove();
    }


    // Prevent duplicate display

    const existingDocuments =
        document.querySelectorAll(
            ".document-name"
        );


    for (
        const documentElement
        of existingDocuments
    ) {

        if (
            documentElement.textContent ===
            fileName
        ) {
            return;
        }
    }


    // Create document item

    const documentElement =
        document.createElement("div");


    documentElement.className =
        "document-item";


    documentElement.innerHTML = `
        <span class="document-icon">
            📄
        </span>

        <span class="document-name">
            ${escapeHtml(fileName)}
        </span>
    `;


    documentList.appendChild(
        documentElement
    );
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
// Get File Extension
// ==================================================

function getFileExtension(fileName) {

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
// Remove Welcome Screen
// ==================================================

function removeWelcomeMessage() {

    const welcome =
        document.querySelector(".welcome");


    if (welcome) {
        welcome.remove();
    }
}


// ==================================================
// New Chat
// ==================================================

newChatBtn.addEventListener(
    "click",
    function () {

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

        messageInput.style.height =
            "auto";


        messageInput.focus();
    }
);


// ==================================================
// Auto Resize Textarea
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
// Scroll Chat To Bottom
// ==================================================

function scrollToBottom() {

    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


// ==================================================
// HTML Safety
// ==================================================

function escapeHtml(value) {

    const div =
        document.createElement("div");


    div.textContent =
        value ?? "";


    return div.innerHTML;
}