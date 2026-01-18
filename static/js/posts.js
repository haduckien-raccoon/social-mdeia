/**
 * Global JavaScript cho Posts App
 * File này chứa các hàm dùng chung cho feed.html và post_detail.html
 */

// ========================================
// 1. CSRF TOKEN HELPER
// ========================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Global CSRF token
const csrftoken = getCookie('csrftoken');

// ========================================
// 2. REACTION FUNCTIONS
// ========================================
let reactionTimeout;

function delayShowReactions(postId) {
    clearTimeout(reactionTimeout);
    reactionTimeout = setTimeout(() => {
        const picker = document.getElementById(`reaction-picker-${postId}`);
        if (picker) picker.style.display = 'block';
    }, 500);
}

function hideReactions(postId) {
    clearTimeout(reactionTimeout);
    setTimeout(() => {
        const picker = document.getElementById(`reaction-picker-${postId}`);
        if (picker) picker.style.display = 'none';
    }, 300);
}

function showReactionPicker(postId) {
    const picker = document.getElementById(`reaction-picker-${postId}`);
    if (picker) {
        const isVisible = picker.style.display === 'block';
        // Hide all other pickers
        document.querySelectorAll('.reaction-picker').forEach(p => p.style.display = 'none');
        // Toggle current picker
        picker.style.display = isVisible ? 'none' : 'block';
    }
}

function toggleReaction(postId, type = 'like') {
    const btn = document.getElementById(`btn-post-like-${postId}`);
    const text = document.getElementById(`text-post-like-${postId}`);
    const countSpan = document.getElementById(`reaction-count-${postId}`);
    
    // Hide reaction picker
    const picker = document.getElementById(`reaction-picker-${postId}`);
    if (picker) picker.style.display = 'none';
    
    // Send request
    fetch(`/posts/${postId}/reaction/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `reaction=${type}`
    })
    .then(res => {
        if (!res.ok) throw new Error("Network error");
        return res.json();
    })
    .then(data => {
        // Update UI
        if (data.status === 'added' || data.status === 'changed') {
            btn.classList.add('reaction-active');
            btn.classList.remove('text-muted');
            
            const reactionNames = {
                'like': 'Thích',
                'love': 'Yêu thích',
                'haha': 'Haha',
                'sad': 'Buồn',
                'angry': 'Phẫn nộ'
            };
            text.innerText = reactionNames[type] || 'Thích';
        } else {
            btn.classList.remove('reaction-active');
            btn.classList.add('text-muted');
            text.innerText = "Thích";
        }
        
        // Update count
        if (countSpan && data.total_count !== undefined) {
            countSpan.innerText = data.total_count;
        }
    })
    .catch(err => {
        console.error('Reaction error:', err);
        alert('Có lỗi xảy ra. Vui lòng thử lại.');
    });
}

// ========================================
// 3. POST ACTIONS
// ========================================
function sharePost(postId) {
    const caption = prompt("Viết lời nhắn khi chia sẻ (tùy chọn):");
    if (caption !== null) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/posts/${postId}/share/`;
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrftoken;
        
        const captionInput = document.createElement('input');
        captionInput.type = 'hidden';
        captionInput.name = 'caption';
        captionInput.value = caption;
        
        form.appendChild(csrfInput);
        form.appendChild(captionInput);
        document.body.appendChild(form);
        form.submit();
    }
}

function deletePost(postId) {
    if (confirm("Bạn có chắc muốn xóa bài viết này?")) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/posts/${postId}/delete/`;
        
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrftoken;
        
        form.appendChild(csrfInput);
        document.body.appendChild(form);
        form.submit();
    }
}

// ========================================
// 4. COMMENT FUNCTIONS (for post_detail.html)
// ========================================
// --- 2. HÀM GỬI COMMENT (Đã sửa ID) ---
function submitComment(parentId = null) {
    // SỬA LỖI 1: Đồng bộ ID giữa HTML và JS
    // Nếu là comment chính (không có parentId) -> dùng id "main-comment-input"
    const inputId = parentId ? `reply-input-${parentId}` : 'main-comment-input';
    
    const contentInput = document.getElementById(inputId);
    if (!contentInput) {
        console.error("Không tìm thấy ô nhập liệu với ID:", inputId);
        return;
    }

    const content = contentInput.value.trim();
    const filesInput = document.getElementById('comment-files'); // Input file ẩn (nếu có)

    // Kiểm tra dữ liệu rỗng
    if (!content && (!filesInput || filesInput.files.length === 0)) {
        return;
    }

    let formData = new FormData();
    formData.append('content', content);
    if (parentId) formData.append('parent_id', parentId);
    
    // Chỉ gửi file nếu là comment chính (form phụ thường không có nút attach file)
    if (!parentId && filesInput) {
        for (let i = 0; i < filesInput.files.length; i++) {
            formData.append('images', filesInput.files[i]);
        }
    }

    // Gửi Ajax
    fetch(`/posts/${POST_ID}/comment/`, {
        method: 'POST',
        headers: { 
            'X-CSRFToken': csrftoken 
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Gửi thất bại");
        return response.json();
    })
    .then(data => {
        console.log("Thành công:", data);
        // Xóa nội dung sau khi gửi thành công
        contentInput.value = '';
        
        if (parentId) {
            // Ẩn form trả lời
            const replyBox = document.getElementById(`reply-form-${parentId}`);
            if (replyBox) replyBox.classList.add('d-none');
        } else {
            // Reset form chính
            if (filesInput) filesInput.value = '';
            const preview = document.getElementById('main-preview');
            if (preview) preview.innerHTML = '';
        }
    })
    .catch(error => console.error("Lỗi:", error));
}

// --- 3. ĐẢM BẢO HÀM GLOBAL (Tránh lỗi ReferenceError) ---
window.submitComment = submitComment;

function toggleCommentLike(commentId) {
    fetch(`/posts/comment/${commentId}/reaction/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: 'reaction=like'
    })
    .then(res => res.json())
    .then(data => {
        const linkEl = document.getElementById(`comment-like-${commentId}`);
        if (linkEl) {
            if (data.status === 'added' || data.status === 'changed') {
                linkEl.classList.add('text-primary', 'fw-bold');
                linkEl.classList.remove('text-muted');
            } else {
                linkEl.classList.remove('text-primary', 'fw-bold');
                linkEl.classList.add('text-muted');
            }
        }
    })
    .catch(err => console.error('Comment reaction error:', err));
}

function deleteComment(commentId) {
    if (!confirm("Bạn có chắc muốn xóa bình luận này?")) return;
    
    fetch(`/posts/comment/${commentId}/delete/`, {
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken}
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== 'ok') {
            alert(data.error || 'Có lỗi xảy ra');
        }
    })
    .catch(err => console.error('Delete comment error:', err));
}

function showReply(commentId) {
    const box = document.getElementById(`reply-box-${commentId}`);
    if (box) {
        box.classList.toggle('d-none');
        if (!box.classList.contains('d-none')) {
            const input = box.querySelector('input');
            if (input) input.focus();
        }
    }
}

// ========================================
// 5. UTILITY FUNCTIONS
// ========================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========================================
// 6. GLOBAL EVENT LISTENERS
// ========================================
document.addEventListener('DOMContentLoaded', function() {
    // Close reaction pickers when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.reaction-btn') && !e.target.closest('.reaction-picker')) {
            document.querySelectorAll('.reaction-picker').forEach(p => p.style.display = 'none');
        }
    });
    
    console.log('✅ Posts.js loaded successfully');
});