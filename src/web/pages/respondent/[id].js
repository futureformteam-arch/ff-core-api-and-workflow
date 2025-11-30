import React from 'react';
import { useRouter } from 'next/router';

export default function RespondentPortal() {
    const router = useRouter();
    const { id } = router.query;

    return (
        <div>
            <h1>Respondent Portal {id}</h1>
        </div>
    );
}
