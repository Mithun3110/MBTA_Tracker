                db.session.execute(
                    text(
                        """
                        CALL create_feedback(:user_id, :feedback_text, :rating)
                        """
                    ),
                    {
                        'user_id': user_id,
                        'feedback_text': feedback_text,
                        'rating': int(rating),
                    },
                )