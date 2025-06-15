// Function to add the script to the head
function addChatbotScript() {
    // Create a new script element
    const script = document.createElement('script');
    script.type = 'module';

    // Define the script content
    const scriptContent = `
        import Chatbot from "https://flowisechatbot.blob.core.windows.net/flowisechatbot/web.js"
    Chatbot.init({
        chatflowid: "22a26f6d-eaa8-49b1-812d-36da0ee90fcd",
        apiHost: "https://nginx.livelymoss-756c05ff.southeastasia.azurecontainerapps.io/",
        chatflowConfig: {
            // topK: 2
        },
        theme: {
            button: {
                backgroundColor: "#3B81F6",
                right: 20,
                bottom: 20,
                size: 48, // small | medium | large | number
                dragAndDrop: true,
                iconColor: "white",
                customIconSrc: "https://raw.githubusercontent.com/walkxcode/dashboard-icons/main/svg/google-messages.svg",
            },
            tooltip: {
                showTooltip: true,
                tooltipMessage: 'Hi There 👋!',
                tooltipBackgroundColor: 'black',
                tooltipTextColor: 'white',
                tooltipFontSize: 16,
            },
            chatWindow: {
                showTitle: true,
                title: 'GGR Assistant',
                titleAvatarSrc: 'https://static.vecteezy.com/system/resources/previews/004/996/790/original/robot-chatbot-icon-sign-free-vector.jpg',
                welcomeMessage: 'Hello! This is custom welcome message',
                errorMessage: 'This is a custom error message',
                backgroundColor: "#ffffff",
                height: 700,
                width: 400,
                fontSize: 16,
                poweredByTextColor: "#303235",
                botMessage: {
                    backgroundColor: "#f7f8ff",
                    textColor: "#303235",
                    showAvatar: true,
                    avatarSrc: "https://static.vecteezy.com/system/resources/previews/004/996/790/original/robot-chatbot-icon-sign-free-vector.jpg",
                },
                userMessage: {
                    backgroundColor: "#3B81F6",
                    textColor: "#ffffff",
                    showAvatar: true,
                    avatarSrc: "https://raw.githubusercontent.com/zahidkhawaja/langchain-chat-nextjs/main/public/usericon.png",
                },
                textInput: {
                    placeholder: 'Type your question',
                    backgroundColor: '#ffffff',
                    textColor: '#303235',
                    sendButtonColor: '#3B81F6',
                    maxChars: 500,
                    maxCharsWarningMessage: 'You exceeded the characters limit. Please input less than 50 characters.',
                    autoFocus: true, // If not used, autofocus is disabled on mobile and enabled on desktop. true enables it on both, false disables it on both.
                },
                feedback: {
                    color: '#303235',
                },
                footer: {
                    textColor: '#303235',
                    text: 'Powered by',
                    company: 'Gigarion',
                    companyLink: 'https://gigarion.com/',
                }
            }
        }
    })
    `;

    // Add the script content to the script element
    script.textContent = scriptContent;

    // Append the script element to the head
    document.head.appendChild(script);
    console.log('Chat bot', localStorage.getItem('user_id'))
}

// Call the function to add the script
addChatbotScript();
