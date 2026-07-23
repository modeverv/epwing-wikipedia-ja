;;; lookup-image-url.el --- Web image inline display for Lookup -*- coding: utf-8; lexical-binding: t -*-

;; Author: User Customization
;; Keywords: lookup, image, web

;;; Commentary:

;; Lookup のエントリ表示バッファ (lookup-content-mode) 内に含まれる
;; Web上の画像URL (例: [画像: //upload.wikimedia.org/...]) を検出し、
;; 画像をダウンロードしてバッファ内にインライン表示します。
;;
;; 使い方:
;;   (require 'lookup-image-url)
;;   (lookup-image-url-setup)
;;

;;; Code:

(require 'lookup-vars)
(require 'lookup-content)
(require 'url)
(require 'image)
(require 'cl-lib)

(defgroup lookup-image-url nil
  "Web image inline display for Lookup."
  :group 'lookup)

(defcustom lookup-image-url-cache-dir
  (expand-file-name "lookup-image-cache" user-emacs-directory)
  "Directory to cache downloaded images."
  :type 'directory
  :group 'lookup-image-url)

(defcustom lookup-image-url-max-width 400
  "Maximum width of displayed inline images in pixels."
  :type 'integer
  :group 'lookup-image-url)

(defcustom lookup-image-url-auto-fetch t
  "Whether to automatically fetch and display inline images in content buffer."
  :type 'boolean
  :group 'lookup-image-url)

(defvar lookup-image-url-pattern
  "\\(?:[\\[【]画像[:|] *\\(?1:[^]\n\r\t\"'>】]+\\)[\\]】]\\|\\(?1:https?://[^ \t\n\r\"'>]+\\.\\(?:png\\|jpg\\|jpeg\\|gif\\|svg\\|webp\\)\\)\\|\\(?1://[^ \t\n\r\"'>]+\\.\\(?:png\\|jpg\\|jpeg\\|gif\\|svg\\|webp\\)\\)\\)"
  "Regexp pattern to match image URLs in Lookup content buffer.")

(defun lookup-image-url--normalize-url (url)
  "Ensure URL starts with scheme."
  (let ((trimmed (string-trim url)))
    (if (string-prefix-p "//" trimmed)
        (concat "https:" trimmed)
      trimmed)))

(defun lookup-image-url--cache-file (url)
  "Return cache file path for URL."
  (unless (file-exists-p lookup-image-url-cache-dir)
    (make-directory lookup-image-url-cache-dir t))
  (let ((hash (sha1 url)))
    (expand-file-name hash lookup-image-url-cache-dir)))

(defun lookup-image-url-fetch-file (url)
  "Fetch URL to cache file and return the file path if successful."
  (let* ((full-url (lookup-image-url--normalize-url url))
         (cache-path (lookup-image-url--cache-file full-url)))
    (if (file-exists-p cache-path)
        cache-path
      (condition-case err
          (progn
            (url-copy-file full-url cache-path t)
            cache-path)
        (error
         (message "lookup-image-url download failed: %s (%s)" full-url err)
         nil)))))

;;;###autoload
(defun lookup-image-url-render-buffer ()
  "Find image URLs in current buffer and render them as inline images."
  (interactive)
  (when (and (display-images-p)
             (derived-mode-p 'lookup-content-mode))
    (save-excursion
      (goto-char (point-min))
      (let ((inhibit-read-only t))
        (while (re-search-forward lookup-image-url-pattern nil t)
          (let* ((match-start (match-beginning 0))
                 (match-end (match-end 0))
                 (raw-url (match-string 1)))
            (when (and raw-url (or (string-prefix-p "http" raw-url)
                                   (string-prefix-p "//" raw-url)))
              (let ((file-path (lookup-image-url-fetch-file raw-url)))
                (when (and file-path (file-exists-p file-path))
                  (let ((type (image-type-from-file-header file-path)))
                    (unless type
                      (let ((ext (file-name-extension raw-url)))
                        (setq type (cond ((string-equal ext "png") 'png)
                                         ((member ext '("jpg" "jpeg")) 'jpeg)
                                         ((string-equal ext "gif") 'gif)
                                         ((string-equal ext "svg") 'svg)
                                         (t nil)))))
                    (when (and type (image-type-available-p type))
                      (let* ((img (create-image file-path type nil
                                                :max-width lookup-image-url-max-width))
                             (ov (make-overlay match-start match-end)))
                        (overlay-put ov 'lookup-image-url t)
                        (overlay-put ov 'display img)))))))))))))

;;;###autoload
(defun lookup-image-url-clear-overlays ()
  "Remove all image overlays in current buffer."
  (interactive)
  (let ((inhibit-read-only t))
    (remove-overlays (point-min) (point-max) 'lookup-image-url t)))

;;;###autoload
(defun lookup-image-url-toggle ()
  "Toggle inline image display in current buffer."
  (interactive)
  (let ((overlays (overlays-in (point-min) (point-max))))
    (if (cl-some (lambda (ov) (overlay-get ov 'lookup-image-url)) overlays)
        (lookup-image-url-clear-overlays)
      (lookup-image-url-render-buffer))))

;;;###autoload
(defun lookup-image-url-setup ()
  "Setup `lookup-image-url` to automatically run in `lookup-content-mode`."
  (interactive)
  (add-hook 'lookup-content-mode-hook #'lookup-image-url-on-content-mode))

(defun lookup-image-url-on-content-mode ()
  "Hook function for `lookup-content-mode-hook'."
  (when lookup-image-url-auto-fetch
    (lookup-image-url-render-buffer)))

(provide 'lookup-image-url)

;;; lookup-image-url.el ends here
